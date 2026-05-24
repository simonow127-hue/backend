from pydantic import BaseModel, Field
from typing import Optional, List
import uuid


class CustomerPayload(BaseModel):
    full_name: str = Field(..., min_length=3)
    phone: str
    phone_e164: Optional[str] = None


class CartItemPayload(BaseModel):
    product_id: str
    slug: str
    name: str
    offer_pieces: int = Field(..., ge=1, le=3)
    quantity: int = Field(default=1, ge=1)
    unit_bundle_price: int
    total: int


class TotalsPayload(BaseModel):
    subtotal: int
    shipping: int = 0
    total: int
    currency: str = "MAD"


class SourcePayload(BaseModel):
    landing_url: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    fbclid: Optional[str] = None
    ttclid: Optional[str] = None
    sc_click_id: Optional[str] = None


class TrackingPayload(BaseModel):
    event_id: Optional[str] = None
    fbp: Optional[str] = None
    fbc: Optional[str] = None
    ttp: Optional[str] = None
    scid: Optional[str] = None


class CreateOrderRequest(BaseModel):
    customer: CustomerPayload
    items: List[CartItemPayload]
    totals: TotalsPayload
    source: Optional[SourcePayload] = None
    tracking: Optional[TrackingPayload] = None


class UpsellRecommendation(BaseModel):
    recommended_product_id: str
    offer_pieces: int
    price_mad: int


class CreateOrderResponse(BaseModel):
    ok: bool = True
    order_id: str
    order_code: str
    upsell: Optional[UpsellRecommendation] = None


class UpsellItemPayload(BaseModel):
    product_id: str
    slug: str
    name: str
    offer_pieces: int = Field(..., ge=1, le=3)
    price_mad: int


class UpsellOrderRequest(BaseModel):
    item: UpsellItemPayload


class UpsellOrderResponse(BaseModel):
    ok: bool = True
    order_id: str
    order_code: str
    new_total_mad: int
