import logging
from zoneinfo import ZoneInfo

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.catalog.products import catalog_entry
from app.core.config import settings

logger = logging.getLogger("riads.sheets")

_CASABLANCA = ZoneInfo("Africa/Casablanca")


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


def _build_sheet_payload(order) -> dict:
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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True,
)
async def _post_to_sheets(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(settings.GOOGLE_SHEETS_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        return response.json()


async def send_order_to_sheets(order, event_type: str = "ORDER_CREATED") -> bool:
    del event_type  # kept for callers; sheet always receives one flat row
    if not settings.ENABLE_SHEETS_WEBHOOK or not settings.GOOGLE_SHEETS_WEBHOOK_URL:
        logger.info("Sheets webhook disabled or not configured — skipping.")
        return False

    payload = _build_sheet_payload(order)
    try:
        result = await _post_to_sheets(payload)
        logger.info("Sheets webhook success for %s: %s", order.order_code, result)
        return True
    except Exception as exc:
        logger.error("Sheets webhook failed for %s: %s", order.order_code, exc)
        return False
