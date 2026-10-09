from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal


PhoneCountry = Literal["SA", "AE"]
Currency = Literal["SAR", "AED"]


class CustomerPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(..., min_length=3, max_length=150)
    phone: str = Field(..., min_length=5, max_length=30)
    phone_e164: Optional[str] = None
    country: PhoneCountry


class CartItemPayload(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=200)
    name: str = Field(..., min_length=1, max_length=250)
    offer_pieces: int = Field(..., ge=1, le=3)
    quantity: int = Field(default=1, ge=1, le=100)
    unit_bundle_price: int = Field(..., ge=0)
    total: int = Field(..., ge=0)


class TotalsPayload(BaseModel):
    subtotal: int = Field(..., ge=0)
    shipping: int = Field(default=0, ge=0)
    total: int = Field(..., ge=0)
    currency: Currency


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
    gclid: Optional[str] = None


class TrackingPayload(BaseModel):
    event_id: Optional[str] = None
    fbp: Optional[str] = None
    fbc: Optional[str] = None
    ttp: Optional[str] = None
    scid: Optional[str] = None


class CreateOrderRequest(BaseModel):
    customer: CustomerPayload
    items: List[CartItemPayload] = Field(..., min_length=1)
    totals: TotalsPayload
    source: Optional[SourcePayload] = None
    tracking: Optional[TrackingPayload] = None


class UpsellRecommendation(BaseModel):
    recommended_product_id: str
    offer_pieces: int = Field(..., ge=1, le=3)
    price_mad: int = Field(..., ge=0)


class CreateOrderResponse(BaseModel):
    ok: bool = True
    order_id: str
    order_code: str
    upsell: Optional[UpsellRecommendation] = None


class UpsellItemPayload(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=200)
    name: str = Field(..., min_length=1, max_length=250)
    offer_pieces: int = Field(..., ge=1, le=3)
    price_mad: int = Field(..., ge=0)


class UpsellOrderRequest(BaseModel):
    item: UpsellItemPayload


class UpsellOrderResponse(BaseModel):
    ok: bool = True
    order_id: str
    order_code: str
    new_total_mad: int
