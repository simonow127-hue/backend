from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    ok: bool = True
    token: str
    expires_in_hours: int


class MetricsDailyPoint(BaseModel):
    date: str
    clicks: int
    sessions: int
    orders: int
    revenue_mad: int


class MetricsChannelRow(BaseModel):
    channel: str
    clicks: int
    orders: int
    revenue_mad: int
    conversion_rate: float


class AdminMetricsResponse(BaseModel):
    from_date: str
    to_date: str
    clicks: int
    sessions: int
    product_views: int
    add_to_carts: int
    checkouts: int
    orders: int
    revenue_mad: int
    average_order_value_mad: float
    conversion_rate: float
    upsell_rate: float
    blocked_events: int
    daily: List[MetricsDailyPoint]
    by_channel: List[MetricsChannelRow]


class AdminOrderListItem(BaseModel):
    id: str
    order_code: str
    status: str
    customer_name: str
    phone_e164: str
    total_mad: int
    upsell_added: bool
    utm_source: Optional[str] = None
    has_ad_click: bool = False
    created_at: datetime


class AdminOrderListResponse(BaseModel):
    items: List[AdminOrderListItem]
    total: int
    page: int
    page_size: int


class AdminOrderDetailResponse(BaseModel):
    id: str
    order_code: str
    status: str
    customer_name: str
    phone_raw: str
    phone_e164: str
    phone_country: str
    items: List[Dict[str, Any]]
    subtotal_mad: int
    shipping_mad: int
    total_mad: int
    currency: str
    upsell_added: bool
    payment_method: str
    source: Dict[str, Any]
    tracking: Dict[str, Any]
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    event_id: Optional[str] = None
    sheet_sent_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
