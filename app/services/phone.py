import re
import phonenumbers
from phonenumbers import PhoneNumberType


MA_MOBILE_LOCAL = re.compile(r"^(06|07)\d{8}$")
MA_MOBILE_INTL = re.compile(r"^(\+?212)(6|7)\d{8}$")


def validate_and_normalize_moroccan_phone(raw: str) -> dict:
    """
    Validates a Moroccan mobile phone number and returns normalized forms.
    Returns dict with: e164, digits_ma (for Meta/Snap hashing), is_valid, error_code.
    """
    cleaned = raw.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    try:
        parsed = phonenumbers.parse(cleaned, "MA")
        if not phonenumbers.is_valid_number(parsed):
            return _invalid("invalid_phone")

        number_type = phonenumbers.number_type(parsed)
        if number_type not in (PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE):
            return _invalid("not_mobile")

        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        digits_ma = e164.lstrip("+")  # e.g. 212612345678

        return {
            "is_valid": True,
            "e164": e164,
            "digits_ma": digits_ma,
            "error_code": None,
        }
    except phonenumbers.NumberParseException:
        # Fallback regex check
        if MA_MOBILE_LOCAL.match(cleaned):
            digits = "212" + cleaned[1:]
            return {
                "is_valid": True,
                "e164": "+" + digits,
                "digits_ma": digits,
                "error_code": None,
            }
        if MA_MOBILE_INTL.match(cleaned):
            stripped = cleaned.lstrip("+")
            if stripped.startswith("212"):
                return {
                    "is_valid": True,
                    "e164": "+" + stripped,
                    "digits_ma": stripped,
                    "error_code": None,
                }
        return _invalid("invalid_phone")


def _invalid(code: str) -> dict:
    return {
        "is_valid": False,
        "e164": None,
        "digits_ma": None,
        "error_code": code,
    }
