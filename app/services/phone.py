import re
from typing import TypedDict, Literal


PhoneCountry = Literal["SA", "AE", "MA"]


class PhoneResult(TypedDict, total=False):
    is_valid: bool
    e164: str
    digits_sa: str
    digits_ae: str
    digits_ma: str
    country: PhoneCountry
    error_code: str


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def validate_and_normalize_phone(
    raw: str,
    country: Literal["SA", "AE"],
) -> PhoneResult:
    """
    Validate and normalize Saudi or UAE mobile numbers.

    SA:
      05XXXXXXXX
      5XXXXXXXX
      9665XXXXXXXX
      +9665XXXXXXXX

    AE:
      05XXXXXXXX
      5XXXXXXXX
      9715XXXXXXXX
      +9715XXXXXXXX
    """

    if not raw or not raw.strip():
        return {
            "is_valid": False,
            "error_code": "phone_empty",
        }

    digits = _digits(raw)

    if country == "SA":
        if len(digits) == 10 and digits.startswith("05"):
            national = digits[1:]
            return {
                "is_valid": True,
                "e164": "+966" + national,
                "digits_sa": national,
                "country": "SA",
            }

        if len(digits) == 9 and digits.startswith("5"):
            return {
                "is_valid": True,
                "e164": "+966" + digits,
                "digits_sa": digits,
                "country": "SA",
            }

        if len(digits) == 12 and digits.startswith("9665"):
            national = digits[3:]
            return {
                "is_valid": True,
                "e164": "+" + digits,
                "digits_sa": national,
                "country": "SA",
            }

        return {
            "is_valid": False,
            "error_code": "invalid_saudi_phone",
        }

    if country == "AE":
        if len(digits) == 10 and digits.startswith("05"):
            national = digits[1:]
            return {
                "is_valid": True,
                "e164": "+971" + national,
                "digits_ae": national,
                "country": "AE",
            }

        if len(digits) == 9 and digits.startswith("5"):
            return {
                "is_valid": True,
                "e164": "+971" + digits,
                "digits_ae": digits,
                "country": "AE",
            }

        if len(digits) == 12 and digits.startswith("9715"):
            national = digits[3:]
            return {
                "is_valid": True,
                "e164": "+" + digits,
                "digits_ae": national,
                "country": "AE",
            }

        return {
            "is_valid": False,
            "error_code": "invalid_uae_phone",
        }

    return {
        "is_valid": False,
        "error_code": "unsupported_country",
    }


# ---------------------------------------------------------
# Morocco compatibility
# ---------------------------------------------------------

def validate_and_normalize_moroccan_phone(
    raw: str,
) -> PhoneResult:
    """
    Keep compatibility with the old Moroccan checkout/backend.

    Supported formats:
      06XXXXXXXX
      07XXXXXXXX
      2126XXXXXXXX
      2127XXXXXXXX
    """

    if not raw or not raw.strip():
        return {
            "is_valid": False,
            "error_code": "phone_empty",
        }

    digits = _digits(raw)

    if len(digits) == 10 and digits.startswith(("06", "07")):
        national = digits[1:]

        return {
            "is_valid": True,
            "e164": "+212" + national,
            "digits_ma": national,
            "country": "MA",
        }

    if len(digits) == 12 and digits.startswith(("2126", "2127")):
        national = digits[3:]

        return {
            "is_valid": True,
            "e164": "+" + digits,
            "digits_ma": national,
            "country": "MA",
        }

    return {
        "is_valid": False,
        "error_code": "invalid_moroccan_phone",
    }


# ---------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------

def validate_and_normalize_saudi_phone(
    raw: str,
) -> PhoneResult:
    return validate_and_normalize_phone(raw, "SA")


def validate_and_normalize_uae_phone(
    raw: str,
) -> PhoneResult:
    return validate_and_normalize_phone(raw, "AE")
