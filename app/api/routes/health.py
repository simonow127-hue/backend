from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.services.sheets import (
    sheets_configured,
    sheets_delivery_mode,
    sheets_webhook_ready,
    _post_to_webhook,
)

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "ok": True,
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "sheets_webhook_enabled": settings.ENABLE_SHEETS_WEBHOOK,
        "sheets_configured": sheets_configured(),
        "sheets_mode": sheets_delivery_mode(),
        "spreadsheet_id": settings.GOOGLE_SHEETS_SPREADSHEET_ID,
    }


@router.post("/health/sheets-test")
async def sheets_test():
    """Send one test row to Google Sheets (delete row with orderid riads-test-* after)."""
    if not sheets_webhook_ready():
        return {"ok": False, "error": "GOOGLE_SHEETS_WEBHOOK_URL not set"}

    orderid = f"riads-test-{datetime.now(timezone.utc).strftime('%H%M%S')}"
    payload = {
        "date": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        "orderid": orderid,
        "country": "Saudi Arabia",
        "name": "Test Riads",
        "phone": "0600000000",
        "product": "Test product",
        "sku": "TEST-SKU",
        "quantity": "1",
        "total_price": 159,
        "currency": "SAR",
        "status": "",
    }
    try:
        result = await _post_to_webhook(payload)
        return {"ok": True, "orderid": orderid, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
