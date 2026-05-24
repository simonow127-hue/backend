import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.order import (
    CreateOrderRequest,
    CreateOrderResponse,
    UpsellOrderRequest,
    UpsellOrderResponse,
    UpsellRecommendation,
)
from app.services.geoip import check_ip
from app.services.orders import _compute_upsell, apply_upsell, create_order

logger = logging.getLogger("riads.api.orders")
router = APIRouter()

# Arabic messages shown to blocked customers
GEO_BLOCK_MESSAGES = {
    "country_blocked": "عذراً، خدمتنا متوفرة حالياً داخل المغرب فقط.",
    "vpn": "غير قادرين على معالجة الطلب من شبكة VPN/Proxy. المرجو تعطيل الـ VPN والمحاولة مجدداً.",
    "tor": "غير قادرين على معالجة الطلب من هذه الشبكة. المرجو استعمال اتصال عادي.",
    "hosting": "غير قادرين على معالجة الطلب من هذا الاتصال. المرجو استعمال اتصال شخصي.",
}


def _extract_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else None


@router.post("/orders", response_model=CreateOrderResponse)
async def post_order(
    payload: CreateOrderRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    geo = await check_ip(client_ip)
    if not geo.allowed:
        logger.warning(
            "Order blocked by geo guard: ip=%s reason=%s country=%s detail=%s",
            client_ip, geo.reason_code, geo.country_iso, geo.detail,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "code": f"geo_{geo.reason_code}",
                "message_ar": GEO_BLOCK_MESSAGES.get(
                    geo.reason_code,
                    "غير قادرين على معالجة هذا الطلب حالياً.",
                ),
            },
        )

    order = await create_order(db, payload, client_ip, user_agent)
    items_data = order.items if isinstance(order.items, list) else []
    upsell_data = _compute_upsell(items_data)

    upsell = UpsellRecommendation(**upsell_data) if upsell_data else None

    return CreateOrderResponse(
        ok=True,
        order_id=str(order.id),
        order_code=order.order_code,
        upsell=upsell,
    )


@router.patch("/orders/{order_id}/upsell", response_model=UpsellOrderResponse)
async def patch_order_upsell(
    order_id: str,
    payload: UpsellOrderRequest,
    db: AsyncSession = Depends(get_db),
):
    order = await apply_upsell(db, order_id, payload.item)
    return UpsellOrderResponse(
        ok=True,
        order_id=str(order.id),
        order_code=order.order_code,
        new_total_mad=order.total_mad,
    )
