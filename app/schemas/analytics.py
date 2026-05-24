from pydantic import BaseModel
from typing import Optional, Dict, Any


class AnalyticsEventRequest(BaseModel):
    event_name: str
    event_id: str
    order_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class AnalyticsEventResponse(BaseModel):
    ok: bool = True
    event_id: str
