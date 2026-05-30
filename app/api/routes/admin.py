import uuid
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db_errors import raise_if_db_error
from app.core.admin_auth import (
    admin_configured,
    create_admin_token,
    require_admin,
    verify_admin_credentials,
)
from app.core.config import settings
from app.core.database import get_db
from app.models.order import Order
from app.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminMetricsResponse,
    AdminOrderDetailResponse,
    AdminOrderListItem,
    AdminOrderListResponse,
)
from app.services.admin_metrics import get_admin_metrics

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/auth/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLoginRequest):
    if not admin_configured():
        raise HTTPException(
            status_code=503,
            detail={"code": "admin_not_configured", "message": "Set ADMIN_USERNAME and ADMIN_PASSWORD"},
        )
    if not verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail={"code": "invalid_credentials"})
    return AdminLoginResponse(
        token=create_admin_token(payload.username),
        expires_in_hours=settings.ADMIN_TOKEN_TTL_HOURS,
    )


@router.get("/metrics", response_model=AdminMetricsResponse)
async def admin_metrics(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    to_d = to_date or today
    from_d = from_date or (to_d - timedelta(days=6))
    if from_d > to_d:
        raise HTTPException(status_code=400, detail={"code": "invalid_date_range"})
    try:
        return await get_admin_metrics(db, from_d, to_d)
    except Exception as exc:
        raise_if_db_error(exc)


@router.get("/orders", response_model=AdminOrderListResponse)
async def admin_list_orders(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(Order)
    count_q = select(func.count()).select_from(Order)

    if from_date:
        start = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
        q = q.where(Order.created_at >= start)
        count_q = count_q.where(Order.created_at >= start)
    if to_date:
        end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        q = q.where(Order.created_at < end)
        count_q = count_q.where(Order.created_at < end)
    if status:
        q = q.where(Order.status == status)
        count_q = count_q.where(Order.status == status)
    if search:
        term = f"%{search.strip()}%"
        filt = (
            Order.order_code.ilike(term)
            | Order.customer_name.ilike(term)
            | Order.phone_e164.ilike(term)
            | Order.phone_raw.ilike(term)
        )
        q = q.where(filt)
        count_q = count_q.where(filt)

    try:
        total = (await db.execute(count_q)).scalar() or 0
        offset = (page - 1) * page_size
        rows = (
            await db.execute(
                q.order_by(Order.created_at.desc()).offset(offset).limit(page_size)
            )
        ).scalars().all()
    except Exception as exc:
        raise_if_db_error(exc)

    items: list[AdminOrderListItem] = []
    for o in rows:
        src = o.source if isinstance(o.source, dict) else {}
        items.append(
            AdminOrderListItem(
                id=str(o.id),
                order_code=o.order_code,
                status=o.status,
                customer_name=o.customer_name,
                phone_e164=o.phone_e164,
                total_mad=o.total_mad,
                upsell_added=bool(o.upsell_added),
                utm_source=src.get("utm_source"),
                has_ad_click=bool(
                    src.get("fbclid") or src.get("ttclid") or src.get("sc_click_id")
                ),
                created_at=o.created_at,
            )
        )

    return AdminOrderListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/orders/{order_id}", response_model=AdminOrderDetailResponse)
async def admin_get_order(
    order_id: str,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        oid = uuid.UUID(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "invalid_order_id"}) from exc

    try:
        order = await db.get(Order, oid)
    except Exception as exc:
        raise_if_db_error(exc)
    if not order:
        raise HTTPException(status_code=404, detail={"code": "order_not_found"})

    items = order.items if isinstance(order.items, list) else []
    return AdminOrderDetailResponse(
        id=str(order.id),
        order_code=order.order_code,
        status=order.status,
        customer_name=order.customer_name,
        phone_raw=order.phone_raw,
        phone_e164=order.phone_e164,
        phone_country=order.phone_country,
        items=items,
        subtotal_mad=order.subtotal_mad,
        shipping_mad=order.shipping_mad,
        total_mad=order.total_mad,
        currency=order.currency,
        upsell_added=bool(order.upsell_added),
        payment_method=order.payment_method,
        source=order.source if isinstance(order.source, dict) else {},
        tracking=order.tracking if isinstance(order.tracking, dict) else {},
        client_ip=order.client_ip,
        user_agent=order.user_agent,
        event_id=order.event_id,
        sheet_sent_at=order.sheet_sent_at,
        notes=order.notes,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
