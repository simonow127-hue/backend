from fastapi import APIRouter

from app.core.config import settings
from app.services.sheets import sheets_configured, sheets_delivery_mode

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
