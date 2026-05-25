from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import APIRouter

from app.core.config import settings
from app.services.sheets import send_order_to_sheets, sheets_any_ready, sheets_webhook_ready
from app.services.sheets_direct import direct_sheets_ready

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "ok": True,
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "sheets_webhook_enabled": settings.ENABLE_SHEETS_WEBHOOK,
        "sheets_webhook_configured": sheets_webhook_ready(),
        "sheets_api_configured": direct_sheets_ready(settings),
        "sheets_ready": sheets_any_ready(),
        "google_sheet_id": settings.GOOGLE_SHEET_ID or None,
    }


@router.post("/health/sheets-test")
async def sheets_test():
    """Append one test row (after GOOGLE_SERVICE_ACCOUNT_JSON or webhook URL is set)."""
    if not sheets_any_ready():
        return {
            "ok": False,
            "error": "sheets_not_configured",
            "hint": "Set GOOGLE_SHEETS_WEBHOOK_URL or GOOGLE_SERVICE_ACCOUNT_JSON in Easypanel",
        }

    test_order = SimpleNamespace(
        order_code="riads-test-row",
        created_at=datetime.now(timezone.utc),
        customer_name="Test Riads",
        phone_raw="0600000000",
        items=[
            {
                "product_id": "nour",
                "offer_pieces": 1,
            }
        ],
        total_mad=199,
        currency="MAD",
    )
    ok = await send_order_to_sheets(test_order)
    return {"ok": ok, "order_code": test_order.order_code}
