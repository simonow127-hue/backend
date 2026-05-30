import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.analytics_event import AnalyticsEvent
from app.schemas.analytics import AnalyticsEventRequest, AnalyticsEventResponse
from app.services.geoip import evaluate_traffic_ip

router = APIRouter()


def _extract_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else None


@router.post("/analytics/events", response_model=AnalyticsEventResponse)
async def track_event(
    payload: AnalyticsEventRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    geo = await evaluate_traffic_ip(client_ip, db)

    full_payload = {
        **(payload.payload or {}),
        "client_ip": client_ip,
        "user_agent": user_agent,
    }

    event = AnalyticsEvent(
        event_name=payload.event_name,
        event_id=payload.event_id,
        order_id=uuid.UUID(payload.order_id) if payload.order_id else None,
        payload=full_payload,
        platform_results={},
        client_ip=client_ip,
        geo_valid=geo.allowed,
        geo_reason=geo.reason_code,
    )
    db.add(event)
    await db.commit()

    return AnalyticsEventResponse(ok=True, event_id=payload.event_id)
