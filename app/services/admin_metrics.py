from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics_event import AnalyticsEvent
from app.models.order import Order
from app.schemas.admin import (
    AdminMetricsResponse,
    MetricsChannelRow,
    MetricsDailyPoint,
)


def _day_bounds(from_date: date, to_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return start, end


def _channel_label(source: dict | None) -> str:
    if not source:
        return "direct"
    if source.get("fbclid"):
        return "meta"
    if source.get("ttclid"):
        return "tiktok"
    if source.get("sc_click_id"):
        return "snap"
    utm = (source.get("utm_source") or "").strip().lower()
    return utm or "organic"


async def get_admin_metrics(
    db: AsyncSession,
    from_date: date,
    to_date: date,
) -> AdminMetricsResponse:
    start, end = _day_bounds(from_date, to_date)
    geo_ok = and_(AnalyticsEvent.geo_valid.is_(True))

    def _count_event(name: str):
        return func.count().filter(
            and_(AnalyticsEvent.event_name == name, geo_ok)
        )

    analytics_base = and_(
        AnalyticsEvent.created_at >= start,
        AnalyticsEvent.created_at < end,
    )
    analytics_row = (
        await db.execute(
            select(
                _count_event("AdClick").label("clicks"),
                _count_event("PageView").label("sessions"),
                _count_event("ViewContent").label("product_views"),
                _count_event("AddToCart").label("add_to_carts"),
                _count_event("InitiateCheckout").label("checkouts"),
                func.count().filter(AnalyticsEvent.geo_valid.is_(False)).label("blocked"),
            )
            .select_from(AnalyticsEvent)
            .where(analytics_base)
        )
    ).one()

    orders_q = select(Order).where(
        and_(Order.created_at >= start, Order.created_at < end)
    )
    orders = (await db.execute(orders_q)).scalars().all()

    orders_count = len(orders)
    revenue = sum(o.total_mad for o in orders)
    upsells = sum(1 for o in orders if o.upsell_added)

    clicks = int(analytics_row.clicks or 0)
    sessions = int(analytics_row.sessions or 0)
    denominator = clicks if clicks > 0 else sessions
    conversion = (orders_count / denominator * 100) if denominator > 0 else 0.0
    aov = (revenue / orders_count) if orders_count > 0 else 0.0
    upsell_rate = (upsells / orders_count * 100) if orders_count > 0 else 0.0

    daily: list[MetricsDailyPoint] = []
    day = from_date
    while day <= to_date:
        d_start, d_end = _day_bounds(day, day)
        day_analytics = (
            await db.execute(
                select(
                    _count_event("AdClick"),
                    _count_event("PageView"),
                )
                .select_from(AnalyticsEvent)
                .where(
                    and_(
                        AnalyticsEvent.created_at >= d_start,
                        AnalyticsEvent.created_at < d_end,
                    )
                )
            )
        ).one()
        day_orders = [o for o in orders if d_start <= o.created_at < d_end]
        daily.append(
            MetricsDailyPoint(
                date=day.isoformat(),
                clicks=int(day_analytics[0] or 0),
                sessions=int(day_analytics[1] or 0),
                orders=len(day_orders),
                revenue_mad=sum(o.total_mad for o in day_orders),
            )
        )
        day += timedelta(days=1)

    channel_stats: dict[str, dict[str, Any]] = {}
    for o in orders:
        ch = _channel_label(o.source if isinstance(o.source, dict) else None)
        if ch not in channel_stats:
            channel_stats[ch] = {"orders": 0, "revenue_mad": 0, "clicks": 0}
        channel_stats[ch]["orders"] += 1
        channel_stats[ch]["revenue_mad"] += o.total_mad

    click_events = (
        await db.execute(
            select(AnalyticsEvent.payload).where(
                and_(
                    AnalyticsEvent.event_name == "AdClick",
                    geo_ok,
                    AnalyticsEvent.created_at >= start,
                    AnalyticsEvent.created_at < end,
                )
            )
        )
    ).scalars().all()
    for payload in click_events:
        if not isinstance(payload, dict):
            continue
        ch = _channel_label(payload)
        if ch not in channel_stats:
            channel_stats[ch] = {"orders": 0, "revenue_mad": 0, "clicks": 0}
        channel_stats[ch]["clicks"] += 1

    by_channel: list[MetricsChannelRow] = []
    for ch, stats in sorted(channel_stats.items(), key=lambda x: -x[1]["revenue_mad"]):
        ch_clicks = stats["clicks"]
        ch_orders = stats["orders"]
        ch_conv = (ch_orders / ch_clicks * 100) if ch_clicks > 0 else 0.0
        by_channel.append(
            MetricsChannelRow(
                channel=ch,
                clicks=ch_clicks,
                orders=ch_orders,
                revenue_mad=stats["revenue_mad"],
                conversion_rate=round(ch_conv, 2),
            )
        )

    return AdminMetricsResponse(
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        clicks=clicks,
        sessions=sessions,
        product_views=int(analytics_row.product_views or 0),
        add_to_carts=int(analytics_row.add_to_carts or 0),
        checkouts=int(analytics_row.checkouts or 0),
        orders=orders_count,
        revenue_mad=revenue,
        average_order_value_mad=round(aov, 2),
        conversion_rate=round(conversion, 2),
        upsell_rate=round(upsell_rate, 2),
        blocked_events=int(analytics_row.blocked or 0),
        daily=daily,
        by_channel=by_channel,
    )
