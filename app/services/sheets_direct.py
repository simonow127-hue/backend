import asyncio
import base64
import binascii
import json
import logging
from functools import lru_cache

import phonenumbers
from google.oauth2 import service_account
from googleapiclient.discovery import build
from phonenumbers import NumberParseException

from app.core.config import settings


logger = logging.getLogger("riads.sheets.direct")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

SHEET_RANGE = "A:H"


# ============================================================
# SETTINGS
# ============================================================

def _get_setting(*names: str):
    for name in names:
        value = getattr(settings, name, None)

        if value is not None and value != "":
            return value

    return None


def direct_sheets_ready() -> bool:
    spreadsheet_id = _get_setting(
        "GOOGLE_SHEETS_SPREADSHEET_ID",
    )

    service_account_b64 = _get_setting(
        "GOOGLE_SERVICE_ACCOUNT_JSON_B64",
        "GOOGLE_SERVICE_ACCOUNT_B64",
    )

    service_account_json = _get_setting(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
    )

    return bool(
        spreadsheet_id
        and (
            service_account_b64
            or service_account_json
        )
    )


# ============================================================
# PRICE
# ============================================================

def format_sheet_price(
    amount,
    currency: str = "SAR",
) -> str:
    if amount is None or amount == "":
        return ""

    try:
        value = int(float(amount))
    except (TypeError, ValueError):
        return str(amount)

    code = (currency or "SAR").strip().upper() or "SAR"

    return f"{value} {code}"


# ============================================================
# PHONE
# ============================================================

def format_sheet_phone(
    phone_raw: str = "",
    phone_e164: str | None = None,
    country: str = "SA",
) -> str:
    candidate = (phone_e164 or phone_raw or "").strip()

    if not candidate:
        return ""

    country_code = (country or "SA").strip().upper()

    region_map = {
        "SA": "SA",
        "AE": "AE",
        "MA": "MA",
    }

    region = region_map.get(country_code, "SA")

    try:
        parsed = phonenumbers.parse(candidate, region)

        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.NATIONAL,
            )

    except NumberParseException:
        pass

    except Exception:
        logger.exception(
            "Unexpected phone formatting error: country=%s",
            country_code,
        )

    text = candidate.replace(" ", "")

    if text.startswith("+"):
        text = text[1:]

    return text


# ============================================================
# SERVICE ACCOUNT CREDENTIALS
# ============================================================

def _service_account_info() -> dict:
    b64_value = _get_setting(
        "GOOGLE_SERVICE_ACCOUNT_JSON_B64",
        "GOOGLE_SERVICE_ACCOUNT_B64",
    )

    if b64_value:
        try:
            decoded = base64.b64decode(
                b64_value,
                validate=True,
            ).decode("utf-8")

            info = json.loads(decoded)

            if not isinstance(info, dict):
                raise ValueError(
                    "Service account credentials must be a JSON object"
                )

            return info

        except (
            binascii.Error,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
        ):
            logger.exception(
                "Invalid Google service account base64 credentials"
            )
            raise

    json_value = _get_setting(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
    )

    if json_value:
        try:
            if isinstance(json_value, dict):
                info = json_value
            else:
                info = json.loads(json_value)

            if not isinstance(info, dict):
                raise ValueError(
                    "Service account credentials must be a JSON object"
                )

            return info

        except (json.JSONDecodeError, ValueError):
            logger.exception(
                "Invalid GOOGLE_SERVICE_ACCOUNT_JSON"
            )
            raise

    raise RuntimeError(
        "Google service account credentials are not configured"
    )


# ============================================================
# GOOGLE SHEETS SERVICE
# ============================================================

@lru_cache(maxsize=1)
def _sheets_service():
    info = _service_account_info()

    credentials = service_account.Credentials.from_service_account_info(
        info,
        scopes=SCOPES,
    )

    return build(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False,
    )


# ============================================================
# PAYLOAD TO SHEET ROW
# ============================================================

def payload_to_row(payload: dict) -> list:
    orderid = str(payload.get("orderid", "")).strip()
    product = str(payload.get("product", "")).strip()
    sku = str(payload.get("sku", "")).strip()

    note = orderid

    if product:
        note = f"{note} | {product}" if note else product

    price = payload.get("total_price", "")

    if isinstance(price, (int, float)):
        price = format_sheet_price(
            price,
            payload.get("currency", "SAR"),
        )

    country_code = str(
        payload.get("country_code")
        or payload.get("phone_country")
        or "SA"
    ).strip().upper()

    country_names = {
        "SA": "Saudi Arabia",
        "AE": "United Arab Emirates",
        "MA": "Morocco",
    }

    country_name = (
        payload.get("country")
        or country_names.get(country_code, "Saudi Arabia")
    )

    phone = format_sheet_phone(
        phone_raw=str(payload.get("phone", "")),
        phone_e164=(
            str(payload.get("phone_e164", "")).strip() or None
        ),
        country=country_code,
    )

    return [
        payload.get("date", ""),
        payload.get("name", ""),
        phone,
        country_name,
        sku,
        payload.get("quantity", ""),
        price,
        note,
    ]


# ============================================================
# APPEND ORDER ROW
# ============================================================

async def append_order_row(payload: dict) -> bool:
    if not direct_sheets_ready():
        logger.warning(
            "Direct Google Sheets is not configured. "
            "Check spreadsheet ID and service account credentials."
        )
        return False

    spreadsheet_id = _get_setting(
        "GOOGLE_SHEETS_SPREADSHEET_ID",
    )

    try:
        row = payload_to_row(payload)
        service = _sheets_service()

        def _append():
            return (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=SHEET_RANGE,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body={"values": [row]},
                )
                .execute()
            )

        result = await asyncio.to_thread(_append)

        logger.info(
            "Google Sheets append success: order=%s updatedRange=%s",
            payload.get("orderid"),
            result.get("updates", {}).get("updatedRange", ""),
        )

        return True

    except Exception:
        logger.exception(
            "Google Sheets append failed: order=%s",
            payload.get("orderid"),
        )
        return False
