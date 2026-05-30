"""
MaxMind GeoIP2 Insights + optional IPQualityScore for order guard and analytics.

MaxMind Insights: https://dev.maxmind.com/geoip/docs/web-services
IPQualityScore: https://www.ipqualityscore.com/documentation/proxy-detection/overview
"""
from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ip_geo_cache import IpGeoCache

logger = logging.getLogger("riads.geoip")

MAXMIND_INSIGHTS_URL = "https://geoip.maxmind.com/geoip/v2.1/insights/{ip}"
IPQS_URL = "https://ipqualityscore.com/api/json/ip/{api_key}/{ip}"
REQUEST_TIMEOUT_SEC = 4.0
CACHE_TTL_HOURS = 24


@dataclass
class GeoCheckResult:
    allowed: bool
    reason_code: str
    country_iso: Optional[str] = None
    detail: Optional[str] = None


def _is_private_or_local(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
    except ValueError:
        return True


async def _fetch_maxmind_insights(client_ip: str) -> tuple[Optional[dict], Optional[str]]:
    if not (settings.MAXMIND_ACCOUNT_ID and settings.MAXMIND_LICENSE_KEY):
        return None, "maxmind_not_configured"

    url = MAXMIND_INSIGHTS_URL.format(ip=client_ip)
    auth = (settings.MAXMIND_ACCOUNT_ID, settings.MAXMIND_LICENSE_KEY)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as client:
            response = await client.get(url, auth=auth)
            response.raise_for_status()
            return response.json(), None
    except httpx.HTTPStatusError as e:
        logger.error("MaxMind HTTP %s for ip=%s", e.response.status_code, client_ip)
        return None, f"http_{e.response.status_code}"
    except (httpx.RequestError, ValueError) as e:
        logger.error("MaxMind error for ip=%s: %s", client_ip, e)
        return None, str(e)


async def _fetch_ipqs(client_ip: str) -> tuple[Optional[dict], Optional[str]]:
    if not settings.IPQS_API_KEY:
        return None, None

    url = IPQS_URL.format(api_key=settings.IPQS_API_KEY, ip=client_ip)
    params = {
        "strictness": settings.IPQS_STRICTNESS,
        "allow_public_access_points": "false",
        "fast": "true",
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if not data.get("success", True):
                return None, data.get("message", "ipqs_error")
            return data, None
    except (httpx.HTTPError, ValueError) as e:
        logger.error("IPQS error for ip=%s: %s", client_ip, e)
        return None, str(e)


def _evaluate_traits(
    country: Optional[str],
    traits: dict,
    *,
    for_metrics: bool,
) -> GeoCheckResult:
    """Apply Morocco + VPN/tor/hosting rules from MaxMind traits."""
    allowed_countries = settings.allowed_countries_list
    if allowed_countries and country and country.upper() not in allowed_countries:
        return GeoCheckResult(
            allowed=False,
            reason_code="country_blocked",
            country_iso=country,
        )

    if settings.BLOCK_TOR and traits.get("is_tor_exit_node"):
        return GeoCheckResult(allowed=False, reason_code="tor", country_iso=country)

    if settings.BLOCK_VPN and (
        traits.get("is_anonymous_vpn")
        or traits.get("is_anonymous_proxy")
        or traits.get("is_anonymous")
    ):
        return GeoCheckResult(allowed=False, reason_code="vpn", country_iso=country)

    if settings.BLOCK_HOSTING and traits.get("is_hosting_provider"):
        return GeoCheckResult(allowed=False, reason_code="hosting", country_iso=country)

    if for_metrics and allowed_countries and not country:
        return GeoCheckResult(
            allowed=False,
            reason_code="country_unknown",
            detail="Country could not be determined",
        )

    return GeoCheckResult(allowed=True, reason_code="ok", country_iso=country)


def _evaluate_ipqs(data: dict) -> GeoCheckResult:
    country = (data.get("country_code") or "").upper() or None
    allowed_countries = settings.allowed_countries_list
    if allowed_countries and country and country not in allowed_countries:
        return GeoCheckResult(allowed=False, reason_code="country_blocked", country_iso=country)

    if data.get("vpn") or data.get("proxy") or data.get("tor"):
        return GeoCheckResult(allowed=False, reason_code="vpn", country_iso=country)

    if data.get("is_crawler") or data.get("bot_status"):
        return GeoCheckResult(allowed=False, reason_code="bot", country_iso=country)

    return GeoCheckResult(allowed=True, reason_code="ok", country_iso=country)


async def check_ip(client_ip: Optional[str]) -> GeoCheckResult:
    """Validate order placement IP (honors ENABLE_GEO_RESTRICTION and GEO_FAIL_OPEN)."""
    if not settings.ENABLE_GEO_RESTRICTION:
        return GeoCheckResult(allowed=True, reason_code="disabled")

    if not client_ip:
        return GeoCheckResult(
            allowed=settings.GEO_FAIL_OPEN,
            reason_code="no_ip",
            detail="Client IP not present in request",
        )

    if _is_private_or_local(client_ip):
        return GeoCheckResult(
            allowed=True,
            reason_code="skipped_private_ip",
            detail=f"Private/local IP {client_ip}",
        )

    data, err = await _fetch_maxmind_insights(client_ip)
    if data is None:
        return GeoCheckResult(
            allowed=settings.GEO_FAIL_OPEN,
            reason_code="geo_lookup_failed",
            detail=err,
        )

    country = (data.get("country") or {}).get("iso_code")
    traits = data.get("traits") or {}
    result = _evaluate_traits(country, traits, for_metrics=False)
    if not result.allowed:
        return result

    if settings.IPQS_API_KEY:
        ipqs_data, ipqs_err = await _fetch_ipqs(client_ip)
        if ipqs_data is None:
            if not settings.GEO_FAIL_OPEN:
                return GeoCheckResult(
                    allowed=False,
                    reason_code="ipqs_lookup_failed",
                    detail=ipqs_err,
                )
        else:
            ipqs_result = _evaluate_ipqs(ipqs_data)
            if not ipqs_result.allowed:
                return ipqs_result

    return GeoCheckResult(allowed=True, reason_code="ok", country_iso=country)


async def evaluate_traffic_ip(
    client_ip: Optional[str],
    db: AsyncSession | None = None,
) -> GeoCheckResult:
    """
    Strict geo check for analytics/metrics — Morocco only, no VPN/proxy/tor/hosting.
    Does not fail-open on lookup errors (unlike orders).
    Uses cache when db session is provided.
    """
    if not client_ip:
        return GeoCheckResult(allowed=False, reason_code="no_ip")

    if _is_private_or_local(client_ip):
        return GeoCheckResult(
            allowed=False,
            reason_code="private_ip",
            detail="Local/private IPs are excluded from metrics",
        )

    if db is not None:
        cached = await db.get(IpGeoCache, client_ip)
        if cached:
            return GeoCheckResult(
                allowed=cached.is_valid_traffic,
                reason_code=cached.reason_code,
                country_iso=cached.country_iso,
            )

    data, err = await _fetch_maxmind_insights(client_ip)
    if data is None:
        return GeoCheckResult(allowed=False, reason_code="geo_lookup_failed", detail=err)

    country = (data.get("country") or {}).get("iso_code")
    traits = data.get("traits") or {}
    result = _evaluate_traits(country, traits, for_metrics=True)

    if result.allowed and settings.IPQS_API_KEY:
        ipqs_data, ipqs_err = await _fetch_ipqs(client_ip)
        if ipqs_data is None:
            result = GeoCheckResult(
                allowed=False,
                reason_code="ipqs_lookup_failed",
                detail=ipqs_err,
            )
        else:
            result = _evaluate_ipqs(ipqs_data)

    if db is not None:
        existing = await db.get(IpGeoCache, client_ip)
        if existing:
            existing.country_iso = result.country_iso
            existing.is_valid_traffic = result.allowed
            existing.reason_code = result.reason_code
        else:
            db.add(
                IpGeoCache(
                    ip=client_ip,
                    country_iso=result.country_iso,
                    is_valid_traffic=result.allowed,
                    reason_code=result.reason_code,
                )
            )

    return result
