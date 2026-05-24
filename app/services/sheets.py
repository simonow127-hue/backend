import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger("riads.sheets")


def _build_order_payload(order, event_type: str = "ORDER_CREATED") -> dict:
    items = order.items if isinstance(order.items, list) else []
    source = order.source or {}
    tracking = order.tracking or {}

    return {
        "secret": settings.GOOGLE_SHEETS_WEBHOOK_SECRET,
        "event_type": event_type,
        "order": {
            "order_code": order.order_code,
            "created_at": order.created_at.isoformat() if order.created_at else "",
            "status": order.status,
            "customer_name": order.customer_name,
            "phone_raw": order.phone_raw,
            "phone_e164": order.phone_e164,
            "phone_digits_ma": order.phone_digits_meta_snap,
            "items": items,
            "subtotal_mad": order.subtotal_mad,
            "shipping_mad": order.shipping_mad,
            "total_mad": order.total_mad,
            "currency": order.currency,
            "upsell_added": order.upsell_added,
            "payment_method": order.payment_method,
            "source": source,
            "tracking": tracking,
            "event_id": order.event_id,
            "client_ip": order.client_ip,
            "user_agent": order.user_agent,
            "notes": order.notes,
        },
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
    if not settings.ENABLE_SHEETS_WEBHOOK or not settings.GOOGLE_SHEETS_WEBHOOK_URL:
        logger.info("Sheets webhook disabled or not configured — skipping.")
        return False

    payload = _build_order_payload(order, event_type)
    try:
        result = await _post_to_sheets(payload)
        logger.info("Sheets webhook success for %s: %s", order.order_code, result)
        return True
    except Exception as exc:
        logger.error("Sheets webhook failed for %s: %s", order.order_code, exc)
        return False
