
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.services.sheets import (
    direct_sheets_ready,
    append_order_row,
)

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "ok": True,
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "sheets_configured": direct_sheets_ready(),
        "sheets_mode": "direct",
        "spreadsheet_id": settings.GOOGLE_SHEETS_SPREADSHEET_ID,
    }


@router.post("/health/sheets-test")
async def sheets_test():
    """Append one test row to Google Sheets."""
    if not direct_sheets_ready():
        return {
            "ok": False,
            "error": "Google Sheets direct integration is not configured",
        }

    orderid = (
        "riads-test-"
        + datetime.now(timezone.utc).strftime("%H%M%S")
    )

    payload = {
        "date": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        "orderid": orderid,
        "country": "Saudi Arabia",
        "country_code": "SA",
        "name": "Test Riads",
        "phone": "0500000000",
        "phone_e164": "+966500000000",
        "product": "Test product",
        "sku": "TEST-SKU",
        "quantity": "1",
        "total_price": "159 SAR",
        "currency": "SAR",
        "status": "",
    }

    try:
        success = await append_order_row(payload)

        if not success:
            return {
                "ok": False,
                "error": "Google Sheets append failed; check backend logs",
            }

        return {
            "ok": True,
            "orderid": orderid,
        }

    except Exception:
        return {
            "ok": False,
            "error": "Google Sheets test failed; check backend logs",
        }
