import time
import logging
import httpx
from app.core.config import settings
from app.core.security import hash_phone_meta_snap

logger = logging.getLogger("riads.meta_capi")

META_API_VERSION = "v20.0"
META_ENDPOINT = "https://graph.facebook.com/{version}/{pixel_id}/events"


def _build_purchase_event(order, event_source_url: str) -> dict:
    items = order.items if isinstance(order.items, list) else []
    contents = [
        {
            "id": item.get("product_id", ""),
            "quantity": item.get("offer_pieces", 1),
            "item_price": item.get("total", 0),
        }
        for item in items
    ]

    tracking = order.tracking or {}
    hashed_phone = hash_phone_meta_snap(order.phone_digits_meta_snap)

    user_data: dict = {
        "ph": hashed_phone,
        "client_ip_address": order.client_ip or "",
        "client_user_agent": order.user_agent or "",
    }
    if tracking.get("fbp"):
        user_data["fbp"] = tracking["fbp"]
    if tracking.get("fbc"):
        user_data["fbc"] = tracking["fbc"]

    event: dict = {
        "event_name": "Purchase",
        "event_time": int(time.time()),
        "event_id": order.event_id or str(order.id),
        "action_source": "website",
        "event_source_url": event_source_url,
        "user_data": user_data,
        "custom_data": {
            "currency": "SAR",
            "value": order.total_mad,
            "content_type": "product",
            "contents": contents,
            "order_id": order.order_code,
        },
    }
    return event


async def send_purchase_event(order, event_source_url: str = "") -> dict:
    if not settings.ENABLE_CAPI or not settings.META_PIXEL_ID or not settings.META_ACCESS_TOKEN:
        logger.info("Meta CAPI disabled or not configured — skipping.")
        return {"skipped": True}

    url = META_ENDPOINT.format(version=META_API_VERSION, pixel_id=settings.META_PIXEL_ID)
    payload: dict = {
        "data": [_build_purchase_event(order, event_source_url)],
    }
    if settings.META_TEST_EVENT_CODE:
        payload["test_event_code"] = settings.META_TEST_EVENT_CODE

    params = {"access_token": settings.META_ACCESS_TOKEN}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, params=params)
            result = response.json()
            logger.info(
                "Meta CAPI Purchase sent — order=%s event_id=%s status=%s",
                order.order_code,
                order.event_id,
                response.status_code,
            )
            return result
    except Exception as exc:
        logger.error("Meta CAPI failed for %s: %s", order.order_code, exc)
        return {"error": str(exc)}
