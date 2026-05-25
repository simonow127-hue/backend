from fastapi import APIRouter

from app.core.config import settings
from app.services.sheets import sheets_webhook_ready

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "ok": True,
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "sheets_webhook_enabled": settings.ENABLE_SHEETS_WEBHOOK,
        "sheets_webhook_configured": sheets_webhook_ready(),
    }
