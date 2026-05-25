import asyncio
import logging
from zoneinfo import ZoneInfo

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.catalog.products import catalog_entry
from app.core.config import settings

logger = logging.getLogger("riads.sheets")

_CASABLANCA = ZoneInfo("Africa/Casablanca")


def sheets_webhook_ready() -> bool:
    return bool(settings.ENABLE_SHEETS_WEBHOOK and _normalize_webhook_url())


def sheets_any_ready() -> bool:
    if not settings.ENABLE_SHEETS_WEBHOOK:
        return False
    if sheets_webhook_ready():
        return True
    from app.services.sheets_direct import direct_sheets_ready

    return direct_sheets_ready(settings)


def _normalize_webhook_url() -> str:
    url = (settings.GOOGLE_SHEETS_WEBHOOK_URL or "").strip()
    if not url:
        return ""
    if "/dev" in url:
        url = url.replace("/dev", "/exec")
    return url


def _format_sheet_date(created_at) -> str:
    if not created_at:
        from datetime import datetime, timezone

        created_at = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        from datetime import timezone

        created_at = created_at.replace(tzinfo=timezone.utc)
    local = created_at.astimezone(_CASABLANCA)
    return local.strftime("%d/%m/%Y")


def _slash_join(values: list[str]) -> str:
    return "/".join(values)


def _line_fields(items: list) -> tuple[str, str, str]:
    names: list[str] = []
    skus: list[str] = []
    quantities: list[str] = []

    for item in items:
        product_id = item.get("product_id") or item.get("id") or ""
        entry = catalog_entry(product_id)
        if entry:
            names.append(entry["arabic_name"])
            skus.append(entry["sku"])
        else:
            names.append(item.get("name") or item.get("product_name") or product_id)
            skus.append(item.get("sku") or product_id)
        pieces = item.get("offer_pieces") or item.get("quantity") or 1
        quantities.append(str(int(pieces)))

    return _slash_join(names), _slash_join(skus), _slash_join(quantities)


def build_sheet_payload(order) -> dict:
    items = order.items if isinstance(order.items, list) else []
    product, sku, quantity = _line_fields(items)

    return {
        "date": _format_sheet_date(order.created_at),
        "orderid": order.order_code or "",
        "country": "Morocco",
        "name": order.customer_name or "",
        "phone": order.phone_raw or "",
        "product": product,
        "sku": sku,
        "quantity": quantity,
        "total_price": order.total_mad,
        "currency": order.currency or "MAD",
        "status": "",
    }


# Backwards-compatible alias
_build_sheet_payload = build_sheet_payload


def _parse_apps_script_response(response: httpx.Response) -> dict:
    text = (response.text or "").strip()
    if not text:
        return {"ok": response.is_success}
    try:
        return response.json()
    except Exception:
        if text.startswith("{"):
            import json

            return json.loads(text)
        return {"ok": response.is_success, "raw": text[:500]}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True,
)
async def _post_to_sheets(payload: dict) -> dict:
    url = _normalize_webhook_url()
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code >= 400:
            logger.error(
                "Sheets HTTP %s body=%s",
                response.status_code,
                (response.text or "")[:500],
            )
        response.raise_for_status()
        return _parse_apps_script_response(response)


async def _send_via_webhook(order) -> bool:
    payload = build_sheet_payload(order)
    try:
        result = await _post_to_sheets(payload)
        logger.info("Sheets webhook success for %s: %s", order.order_code, result)
        return True
    except Exception as exc:
        logger.error("Sheets webhook failed for %s: %s", order.order_code, exc)
        return False


async def send_order_to_sheets(order, event_type: str = "ORDER_CREATED") -> bool:
    del event_type
    if not settings.ENABLE_SHEETS_WEBHOOK:
        logger.warning("Sheets disabled (ENABLE_SHEETS_WEBHOOK=false).")
        return False

    if _normalize_webhook_url():
        if await _send_via_webhook(order):
            return True
        logger.warning("Webhook failed for %s — trying Sheets API fallback.", order.order_code)

    from app.services.sheets_direct import append_order_row_sync, direct_sheets_ready

    if direct_sheets_ready(settings):
        return await asyncio.to_thread(append_order_row_sync, order, settings)

    if not _normalize_webhook_url() and not direct_sheets_ready(settings):
        logger.warning(
            "Sheets not configured for %s — set GOOGLE_SHEETS_WEBHOOK_URL or "
            "GOOGLE_SERVICE_ACCOUNT_JSON + GOOGLE_SHEET_ID in Easypanel.",
            order.order_code,
        )
    return False
