from datetime import datetime
from sqlalchemy import Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class IpGeoCache(Base):
    """Cached MaxMind + optional IPQS results for analytics filtering."""

    __tablename__ = "ip_geo_cache"

    ip: Mapped[str] = mapped_column(Text, primary_key=True)
    country_iso: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_valid_traffic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason_code: Mapped[str] = mapped_column(Text, nullable=False, default="unknown")
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
