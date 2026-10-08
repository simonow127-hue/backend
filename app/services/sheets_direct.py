```python
import asyncio
import base64
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
# PRICE
# ============================================================

def format_sheet_price(
    amount,
    currency: str = "SAR",
) -> str:
    """
    Format price for Google Sheets.

    Examples:
        199 -> "199 SAR"
        149 -> "149 AED"
    """

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
    """
    Format customer phone number for Google Sheets.

    Supported countries:
        SA = Saudi Arabia
        AE = United Arab Emirates
        MA = Morocco
    """

    candidate = (phone_e164 or phone_raw or "").strip()

    if not candidate:
        return ""

    region_map = {
        "SA": "SA",
        "AE": "AE",
        "MA": "MA",
    }

    country_code = (country or "SA").strip().upper()
    region = region_map.get(country_code, "SA")

    try:
        parsed = phonenumbers.parse(
            candidate,
            region,
        )

        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.NATIONAL,
            )

    except NumberParseException:
        pass
    except Exception:
        logger.exception(
            "Unexpected error while formatting phone: country=%s",
            country_code,
        )

    # Fallback
    text = candidate.replace(" ", "")

    if text.startswith("+"):
        text = text[1:]

    return text


# ============================================================
# GOOGLE SHEETS CONFIG
# ============================================================

def direct_sheets_ready() -> bool:
    """
    Check if direct Google Sheets integration is configured.
    """

    spreadsheet_id = getattr(
        settings,
        "GOOGLE_SHEETS_SPREADSHEET_ID",
        None,
    )

    service_account_b64 = getattr(
        settings,
        "GOOGLE_SERVICE_ACCOUNT_B64",
        None,
    )

    service_account_json = getattr(
        settings,
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        None,
    )

    return bool(
        spreadsheet_id
        and (
            service_account_b64
            or service_account_json
        )
    )


# ============================================================
# SERVICE ACCOUNT
# ============================================================

def _service_account_info() -> dict:
    """
    Load Google service account credentials.

    Supports:
        GOOGLE_SERVICE_ACCOUNT_B64
        GOOGLE_SERVICE_ACCOUNT_JSON
    """

    b64_value = getattr(
        settings,
        "GOOGLE_SERVICE_ACCOUNT_B64",
        None,
    )

    if b64_value:
        try:
            decoded = base64.b64decode(
                b64_value
            ).decode("utf-8")

            return json.loads(decoded)

        except Exception:
            logger.exception(
                "Failed to decode GOOGLE_SERVICE_ACCOUNT_B64"
            )
            raise

    json_value = getattr(
        settings,
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        None,
    )

    if json_value:
        if isinstance(json_value, dict):
            return json_value

        try:
            return json.loads(json_value)

        except Exception:
            logger.exception(
                "Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON"
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
    """
    Create and cache Google Sheets API client.
    """

    info = _service_account_info()

    credentials = (
        service_account.Credentials.from_service_account_info(
            info,
            scopes=SCOPES,
        )
    )

    return build(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False,
    )


# ============================================================
# PAYLOAD -> SHEET ROW
# ============================================================

def payload_to_row(payload: dict) -> list:
    """
    Convert order payload into one Google Sheets row.

    Expected columns:

        A = date
        B = name
        C = phone
        D = country
        E = sku
        F = quantity
        G = price
        H = note
    """

    orderid = str(
        payload.get("orderid", "")
    ).strip()

    product = str(
        payload.get("product", "")
    ).strip()

    sku = str(
        payload.get("sku", "")
    ).strip()

    # --------------------------------------------------------
    # NOTE
    # --------------------------------------------------------

    note = orderid

    if product:
        if note:
            note = f"{note} | {product}"
        else:
            note = product

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    price = payload.get(
        "total_price",
        "",
    )

    if isinstance(price, (int, float)):
        price = format_sheet_price(
            price,
            payload.get(
                "currency",
                "SAR",
            ),
        )

    # --------------------------------------------------------
    # PHONE
    # --------------------------------------------------------

    phone = format_sheet_phone(
        phone_raw=str(
            payload.get(
                "phone",
                "",
            )
        ),
        phone_e164=(
            str(
                payload.get(
                    "phone_e164",
                    "",
                )
            ).strip()
            or None
        ),
        country=str(
            payload.get(
                "country_code",
                "SA",
            )
        ),
    )

    # --------------------------------------------------------
    # ROW
    # --------------------------------------------------------

    return [
        payload.get(
            "date",
            "",
        ),
        payload.get(
            "name",
            "",
        ),
        phone,
        payload.get(
            "country",
            "Saudi Arabia",
        ),
        sku,
        payload.get(
            "quantity",
            "",
        ),
        price,
        note,
    ]


# ============================================================
# APPEND ROW
# ============================================================

async def append_order_row(
    payload: dict,
) -> bool:
    """
    Append one order row to Google Sheets.

    Returns:
        True  -> success
        False -> failure / not configured
    """

    if not direct_sheets_ready():
        logger.warning(
            "Direct Google Sheets is not configured"
        )
        return False

    spreadsheet_id = getattr(
        settings,
        "GOOGLE_SHEETS_SPREADSHEET_ID",
        None,
    )

    if not spreadsheet_id:
        logger.warning(
            "GOOGLE_SHEETS_SPREADSHEET_ID is missing"
        )
        return False

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
                    body={
                        "values": [row],
                    },
                )
                .execute()
            )

        result = await asyncio.to_thread(
            _append
        )

        logger.info(
            "Google Sheets direct append success: order=%s country=%s currency=%s",
            payload.get("orderid"),
            payload.get("country_code"),
            payload.get("currency"),
        )

        return True

    except Exception:
        logger.exception(
            "Google Sheets direct append failed: order=%s",
            payload.get("orderid"),
        )

        return False
```
بعد هاد الملف، خاصنا كذلك نتأكدو أن `sheets.py` كيبعث `country_code`، يعني داخل `build_sheet_payload()` يكون عندك:

```python
"country": country,
"country_code": order.phone_country or "SA",
"currency": currency,
```

وبهاد الشكل:

- 🇸🇦 `SA` → الرقم يتفسر كسعودي + السعر `SAR`
- 🇦🇪 `AE` → الرقم يتفسر كإماراتي + السعر `AED`
- 🇲🇦 `MA` → يبقى مدعوم كذلك
- Google Sheets غادي يستقبل الدولة والعملة الصحيحة.
- ما تبدل حتى حاجة فـ Google credentials أو طريقة الـ append.

**المهم:** قبل ما ندوزو لـ Meta CAPI، خاصنا نراجع `geoip.py` حيث إذا مازال كيسمح غير بـ Morocco، الإمارات والسعودية غادي يتبلوكاو حتى لو كل كود checkout صحيح.
