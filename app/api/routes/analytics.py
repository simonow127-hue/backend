import uuid
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.analytics import AnalyticsEventRequest, AnalyticsEventResponse
from app.models.analytics_event import AnalyticsEvent

router = APIRouter()


@router.post("/analytics/events", response_model=AnalyticsEventResponse)
async def track_event(
    payload: AnalyticsEventRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    user_agent = request.headers.get("User-Agent")

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
    )
    db.add(event)
    await db.commit()

    return AnalyticsEventResponse(ok=True, event_id=payload.event_id)
