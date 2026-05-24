import time
import logging
import httpx
from app.core.config import settings
from app.core.security import hash_phone_meta_snap

logger = logging.getLogger("riads.snap_capi")

SNAP_ENDPOINT = "https://tr.snapchat.com/v3/{pixel_id}/events"


def _build_purchase_event(order, event_source_url: str) -> dict:
    hashed_phone = hash_phone_meta_snap(order.phone_digits_meta_snap)

    event: dict = {
        "event_name": "PURCHASE",
        "event_time": int(time.time()),
        "event_id": order.event_id or str(order.id),
        "action_source": "WEB",
        "event_source_url": event_source_url,
        "user_data": {
            "ph": hashed_phone,
            "client_ip_address": order.client_ip or "",
            "client_user_agent": order.user_agent or "",
        },
        "custom_data": {
            "currency": "MAD",
            "value": order.total_mad,
            "order_id": order.order_code,
        },
    }
    return event


async def send_purchase_event(order, event_source_url: str = "") -> dict:
    if not settings.ENABLE_CAPI or not settings.SNAP_PIXEL_ID or not settings.SNAP_ACCESS_TOKEN:
        logger.info("Snap CAPI disabled or not configured — skipping.")
        return {"skipped": True}

    url = SNAP_ENDPOINT.format(pixel_id=settings.SNAP_PIXEL_ID)
    payload = {
        "data": [_build_purchase_event(order, event_source_url)],
    }
    params = {"access_token": settings.SNAP_ACCESS_TOKEN}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, params=params)
            result = response.json()
            logger.info(
                "Snap CAPI PURCHASE sent — order=%s event_id=%s status=%s",
                order.order_code,
                order.event_id,
                response.status_code,
            )
            return result
    except Exception as exc:
        logger.error("Snap CAPI failed for %s: %s", order.order_code, exc)
        return {"error": str(exc)}
