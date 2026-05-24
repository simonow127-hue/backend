import time
import logging
import httpx
from app.core.config import settings
from app.core.security import hash_phone_tiktok

logger = logging.getLogger("riads.tiktok_capi")

TIKTOK_ENDPOINT = "https://business-api.tiktok.com/open_api/v1.3/event/track/"


def _build_purchase_event(order, page_url: str, referrer: str) -> dict:
    items = order.items if isinstance(order.items, list) else []
    contents = [
        {
            "content_id": item.get("product_id", ""),
            "content_name": item.get("name", ""),
            "quantity": item.get("offer_pieces", 1),
            "price": item.get("total", 0),
        }
        for item in items
    ]

    tracking = order.tracking or {}
    hashed_phone = hash_phone_tiktok(order.phone_e164)

    user: dict = {
        "phone": hashed_phone,
        "ip": order.client_ip or "",
        "user_agent": order.user_agent or "",
    }
    if tracking.get("ttp"):
        user["ttp"] = tracking["ttp"]

    event: dict = {
        "event": "CompletePayment",
        "event_time": int(time.time()),
        "event_id": order.event_id or str(order.id),
        "user": user,
        "properties": {
            "currency": "MAD",
            "value": order.total_mad,
            "content_type": "product",
            "contents": contents,
        },
        "page": {
            "url": page_url,
            "referrer": referrer,
        },
    }
    return event


async def send_purchase_event(order, page_url: str = "", referrer: str = "") -> dict:
    if not settings.ENABLE_CAPI or not settings.TIKTOK_PIXEL_ID or not settings.TIKTOK_ACCESS_TOKEN:
        logger.info("TikTok CAPI disabled or not configured — skipping.")
        return {"skipped": True}

    payload: dict = {
        "event_source": "web",
        "event_source_id": settings.TIKTOK_PIXEL_ID,
        "data": [_build_purchase_event(order, page_url, referrer)],
    }
    if settings.TIKTOK_TEST_EVENT_CODE:
        payload["test_event_code"] = settings.TIKTOK_TEST_EVENT_CODE

    headers = {
        "Access-Token": settings.TIKTOK_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(TIKTOK_ENDPOINT, json=payload, headers=headers)
            result = response.json()
            logger.info(
                "TikTok CAPI CompletePayment sent — order=%s event_id=%s status=%s",
                order.order_code,
                order.event_id,
                response.status_code,
            )
            return result
    except Exception as exc:
        logger.error("TikTok CAPI failed for %s: %s", order.order_code, exc)
        return {"error": str(exc)}
