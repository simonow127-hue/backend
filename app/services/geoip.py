"""
MaxMind GeoIP2 Insights integration for order fraud / geo restriction.

Uses the Insights web service (https://geoip.maxmind.com/geoip/v2.1/insights/{ip})
which returns country + traits (is_anonymous_vpn, is_tor_exit_node, is_hosting_provider, etc.)
authenticated via HTTP Basic auth with MaxMind account_id + license_key.

Docs: https://dev.maxmind.com/geoip/docs/web-services
"""
from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("riads.geoip")

MAXMIND_INSIGHTS_URL = "https://geoip.maxmind.com/geoip/v2.1/insights/{ip}"
REQUEST_TIMEOUT_SEC = 4.0


@dataclass
class GeoCheckResult:
    allowed: bool
    reason_code: str  # e.g. "ok", "country_blocked", "vpn", "tor", "hosting", "geo_lookup_failed", "skipped_private_ip"
    country_iso: Optional[str] = None
    detail: Optional[str] = None


def _is_private_or_local(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
    except ValueError:
        return True  # malformed → treat as private (don't call MaxMind)


async def check_ip(client_ip: Optional[str]) -> GeoCheckResult:
    """
    Validate that an order may be placed from the given IP.

    Returns GeoCheckResult.allowed=True/False with a reason_code.
    Honors settings flags: ENABLE_GEO_RESTRICTION, ALLOWED_COUNTRIES,
    BLOCK_VPN, BLOCK_TOR, BLOCK_HOSTING, GEO_FAIL_OPEN.
    """
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
            detail=f"Private/local IP {client_ip} — skipping geo check",
        )

    if not (settings.MAXMIND_ACCOUNT_ID and settings.MAXMIND_LICENSE_KEY):
        logger.warning("MaxMind credentials not configured — geo check bypassed")
        return GeoCheckResult(
            allowed=settings.GEO_FAIL_OPEN,
            reason_code="maxmind_not_configured",
        )

    url = MAXMIND_INSIGHTS_URL.format(ip=client_ip)
    auth = (settings.MAXMIND_ACCOUNT_ID, settings.MAXMIND_LICENSE_KEY)

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as client:
            response = await client.get(url, auth=auth)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        logger.error("MaxMind API HTTP %s for ip=%s: %s", e.response.status_code, client_ip, e.response.text)
        return GeoCheckResult(
            allowed=settings.GEO_FAIL_OPEN,
            reason_code="geo_lookup_failed",
            detail=f"http_{e.response.status_code}",
        )
    except (httpx.RequestError, ValueError) as e:
        logger.error("MaxMind API error for ip=%s: %s", client_ip, e)
        return GeoCheckResult(
            allowed=settings.GEO_FAIL_OPEN,
            reason_code="geo_lookup_failed",
            detail=str(e),
        )

    country = (data.get("country") or {}).get("iso_code")
    traits = data.get("traits") or {}

    allowed_countries = settings.allowed_countries_list
    if allowed_countries and country and country.upper() not in allowed_countries:
        return GeoCheckResult(
            allowed=False,
            reason_code="country_blocked",
            country_iso=country,
            detail=f"Country {country} not in allowed list {allowed_countries}",
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

    return GeoCheckResult(allowed=True, reason_code="ok", country_iso=country)
