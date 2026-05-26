import uuid
import logging
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order
from app.models.analytics_event import AnalyticsEvent
from app.schemas.order import CreateOrderRequest, UpsellItemPayload
from app.services.phone import validate_and_normalize_moroccan_phone
from app.services import sheets as sheets_service
from app.services import meta_capi, tiktok_events, snapchat_capi
from app.core.config import settings

logger = logging.getLogger("riads.orders")

UPSELL_MAP = {
    "jadr": "nour",
    "nour": "naqaa",
    "naqaa": "nour",
}

UPSELL_PRICES = {
    1: 199,
    2: 279,
    3: 349,
}

def _generate_order_code() -> str:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    short_id = uuid.uuid4().hex[:4].lower()
    return f"riads-{date_str}-{short_id}"


def _compute_upsell(items: list) -> dict | None:
    product_ids = {item.get("product_id") for item in items}
    for pid in product_ids:
        upsell_id = UPSELL_MAP.get(pid)
        if upsell_id and upsell_id not in product_ids:
            return {
                "recommended_product_id": upsell_id,
                "offer_pieces": 1,
                "price_mad": UPSELL_PRICES[1],
            }
    # All products present — upsell quantity upgrade
    return {
        "recommended_product_id": list(product_ids)[0],
        "offer_pieces": 2,
        "price_mad": UPSELL_PRICES[2],
    }


async def create_order(
    db: AsyncSession,
    payload: CreateOrderRequest,
    client_ip: str | None,
    user_agent: str | None,
) -> Order:
    # Validate phone
    phone_result = validate_and_normalize_moroccan_phone(payload.customer.phone)
    if not phone_result["is_valid"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail={
                "code": phone_result["error_code"],
                "message_ar": "المرجو إدخال رقم هاتف مغربي صحيح",
            },
        )

    order_code = _generate_order_code()
    event_id = (payload.tracking.event_id if payload.tracking else None) or str(uuid.uuid4())

    items_data = [item.model_dump() for item in payload.items]
    source_data = payload.source.model_dump() if payload.source else {}
    tracking_data = payload.tracking.model_dump() if payload.tracking else {}
    tracking_data["event_id"] = event_id

    order = Order(
        order_code=order_code,
        status="new",
        customer_name=payload.customer.full_name,
        phone_raw=payload.customer.phone,
        phone_e164=phone_result["e164"],
        phone_digits_meta_snap=phone_result["digits_ma"],
        items=items_data,
        subtotal_mad=payload.totals.subtotal,
        shipping_mad=payload.totals.shipping,
        total_mad=payload.totals.total,
        currency=payload.totals.currency,
        source=source_data,
        tracking=tracking_data,
        event_id=event_id,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    logger.info("Order created: %s", order.order_code)
    return order


async def _load_order(order_id: uuid.UUID) -> Order | None:
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        return await db.get(Order, order_id)


async def _update_sheet_status(order_id: uuid.UUID, *, sent: bool) -> None:
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        order_obj = await db.get(Order, order_id)
        if not order_obj:
            return
        if sent:
            order_obj.sheet_sent_at = datetime.now(timezone.utc)
            order_obj.status = "sent_to_sheet"
        elif order_obj.status == "new":
            order_obj.status = "sheet_failed"
        await db.commit()


async def run_order_side_effects(order_id: uuid.UUID) -> None:
    """Background job: reload order from DB, then Sheets + CAPI."""
    order = await _load_order(order_id)
    if not order:
        logger.error("Side effects skipped — order %s not found", order_id)
        return

    source = order.source or {}
    landing_url = source.get("landing_url") or settings.FRONTEND_URL
    thank_you_url = f"{settings.FRONTEND_URL}/thank-you"

    try:
        results = await asyncio.gather(
            sheets_service.send_order_to_sheets(order),
            meta_capi.send_purchase_event(order, event_source_url=landing_url),
            tiktok_events.send_purchase_event(order, page_url=thank_you_url, referrer=landing_url),
            snapchat_capi.send_purchase_event(order, event_source_url=thank_you_url),
            return_exceptions=True,
        )
    except Exception:
        logger.exception("Side effects crashed for order %s", order.order_code)
        await _update_sheet_status(order_id, sent=False)
        return

    sheets_ok = results[0] is True
    await _update_sheet_status(order_id, sent=sheets_ok)


async def run_sheet_sync_only(order_id: uuid.UUID) -> bool:
    """Send one order to Google Sheets (retry / upsell)."""
    order = await _load_order(order_id)
    if not order:
        return False
    ok = await sheets_service.send_order_to_sheets(order, force=True)
    await _update_sheet_status(order_id, sent=ok)
    return ok


async def apply_upsell(
    db: AsyncSession,
    order_id: str,
    upsell_item: UpsellItemPayload,
) -> Order:
    from fastapi import HTTPException

    order = await db.get(Order, uuid.UUID(order_id))
    if not order:
        raise HTTPException(status_code=404, detail={"code": "order_not_found"})

    if order.upsell_added:
        raise HTTPException(status_code=409, detail={"code": "upsell_already_applied"})

    current_items = list(order.items) if isinstance(order.items, list) else []
    upsell_data = upsell_item.model_dump()
    upsell_data["total"] = upsell_item.price_mad
    current_items.append(upsell_data)

    order.items = current_items
    order.total_mad = order.total_mad + upsell_item.price_mad
    order.subtotal_mad = order.subtotal_mad + upsell_item.price_mad
    order.upsell_added = True
    order.status = "upsell_added"

    await db.commit()
    await db.refresh(order)

    logger.info("Upsell applied to order %s, new total: %s", order.order_code, order.total_mad)
    return order
