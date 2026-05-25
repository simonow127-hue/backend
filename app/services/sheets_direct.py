"""Append order rows via Google Sheets API (no Apps Script webhook required)."""

import json
import logging

from app.services.sheets import build_sheet_payload

logger = logging.getLogger("riads.sheets.direct")

SCOPES = ("https://www.googleapis.com/auth/spreadsheets",)


def _load_credentials(settings):
    raw = (settings.GOOGLE_SERVICE_ACCOUNT_JSON or "").strip()
    if not raw:
        return None
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON: %s", exc)
        return None

    from google.oauth2.service_account import Credentials

    return Credentials.from_service_account_info(info, scopes=SCOPES)


def direct_sheets_ready(settings) -> bool:
    return bool(
        (settings.GOOGLE_SHEET_ID or "").strip()
        and (settings.GOOGLE_SERVICE_ACCOUNT_JSON or "").strip()
    )


def append_order_row_sync(order, settings) -> bool:
    sheet_id = (settings.GOOGLE_SHEET_ID or "").strip()
    if not sheet_id:
        return False

    creds = _load_credentials(settings)
    if not creds:
        return False

    payload = build_sheet_payload(order)
    row = [
        payload["date"],
        payload["orderid"],
        payload["country"],
        payload["name"],
        payload["phone"],
        payload["product"],
        payload["sku"],
        payload["quantity"],
        payload["total_price"],
        payload["currency"],
        payload["status"],
    ]

    try:
        import gspread

        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        _ensure_header(worksheet)
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("Sheets API append OK for %s", order.order_code)
        return True
    except Exception as exc:
        logger.error("Sheets API append failed for %s: %s", order.order_code, exc)
        return False


def _ensure_header(worksheet) -> None:
    headers = [
        "date",
        "orderid",
        "country",
        "name",
        "phone",
        "product",
        "sku",
        "quantity",
        "total price",
        "currency",
        "status",
    ]
    try:
        first = worksheet.row_values(1)
        if not any(str(cell).strip() for cell in first):
            worksheet.update("A1:K1", [headers])
    except Exception:
        logger.warning("Could not ensure sheet header row", exc_info=True)
