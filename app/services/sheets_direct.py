import asyncio
import base64
import json
import logging
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import settings

logger = logging.getLogger("riads.sheets.direct")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_RANGE = "A:K"


def direct_sheets_ready() -> bool:
    return bool(_service_account_info() and (settings.GOOGLE_SHEETS_SPREADSHEET_ID or "").strip())


def _service_account_info() -> dict | None:
    if settings.GOOGLE_SERVICE_ACCOUNT_JSON_B64.strip():
        try:
            raw = base64.b64decode(settings.GOOGLE_SERVICE_ACCOUNT_JSON_B64.strip())
            return json.loads(raw)
        except Exception as exc:
            logger.error("Invalid GOOGLE_SERVICE_ACCOUNT_JSON_B64: %s", exc)
            return None
    if settings.GOOGLE_SERVICE_ACCOUNT_JSON.strip():
        try:
            return json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON.strip())
        except Exception as exc:
            logger.error("Invalid GOOGLE_SERVICE_ACCOUNT_JSON: %s", exc)
            return None
    return None


@lru_cache(maxsize=1)
def _sheets_service():
    info = _service_account_info()
    if not info:
        raise RuntimeError("Service account not configured")
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def payload_to_row(payload: dict) -> list:
    return [
        payload.get("date", ""),
        payload.get("orderid", ""),
        payload.get("country", "Morocco"),
        payload.get("name", ""),
        payload.get("phone", ""),
        payload.get("product", ""),
        payload.get("sku", ""),
        payload.get("quantity", ""),
        payload.get("total_price", ""),
        payload.get("currency", "MAD"),
        payload.get("status", ""),
    ]


def _append_row_sync(payload: dict) -> None:
    spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID.strip()
    service = _sheets_service()
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=SHEET_RANGE,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [payload_to_row(payload)]},
    ).execute()


async def append_order_row(payload: dict) -> bool:
    if not direct_sheets_ready():
        return False
    try:
        await asyncio.to_thread(_append_row_sync, payload)
        logger.info("Sheets API append ok for %s", payload.get("orderid"))
        return True
    except Exception as exc:
        logger.error("Sheets API append failed for %s: %s", payload.get("orderid"), exc)
        return False
