import uuid
from datetime import datetime
from sqlalchemy import Text, Integer, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="new", nullable=False)

    customer_name: Mapped[str] = mapped_column(Text, nullable=False)
    phone_raw: Mapped[str] = mapped_column(Text, nullable=False)
    phone_e164: Mapped[str] = mapped_column(Text, nullable=False)
    phone_digits_meta_snap: Mapped[str] = mapped_column(Text, nullable=False)
    phone_country: Mapped[str] = mapped_column(Text, default="MA")

    items: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    subtotal_mad: Mapped[int] = mapped_column(Integer, nullable=False)
    shipping_mad: Mapped[int] = mapped_column(Integer, default=0)
    total_mad: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(Text, default="MAD")

    upsell_added: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_method: Mapped[str] = mapped_column(Text, default="COD")

    source: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    tracking: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)

    client_ip: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    sheet_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
