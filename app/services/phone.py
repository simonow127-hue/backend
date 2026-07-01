import re
import phonenumbers
from phonenumbers import PhoneNumberType


SA_MOBILE_LOCAL = re.compile(r"^05\d{8}$")
SA_MOBILE_INTL = re.compile(r"^(\+?966)5\d{8}$")


def validate_and_normalize_saudi_phone(raw: str) -> dict:
    """
    Validates a Saudi mobile phone number and returns normalized forms.
    Returns dict with: e164, digits_sa (for Meta/Snap hashing), is_valid, error_code.
    """
    cleaned = raw.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    try:
        parsed = phonenumbers.parse(cleaned, "SA")
        region = phonenumbers.region_code_for_number(parsed)
        if phonenumbers.is_valid_number(parsed) and region == "SA":
            number_type = phonenumbers.number_type(parsed)
            if number_type in (PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE):
                e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                digits_sa = e164.lstrip("+")
                return {
                    "is_valid": True,
                    "e164": e164,
                    "digits_sa": digits_sa,
                    "error_code": None,
                }
    except phonenumbers.NumberParseException:
        pass

    # Fallback: accept 05XXXXXXXX (10 digits) — covers all SA operators incl. 057
    if SA_MOBILE_LOCAL.match(cleaned):
        digits = "966" + cleaned[1:]
        return {
            "is_valid": True,
            "e164": "+" + digits,
            "digits_sa": digits,
            "error_code": None,
        }

    # Accept +9665XXXXXXXX or 9665XXXXXXXX
    if SA_MOBILE_INTL.match(cleaned):
        stripped = cleaned.lstrip("+")
        if not stripped.startswith("966"):
            stripped = "966" + stripped
        return {
            "is_valid": True,
            "e164": "+" + stripped,
            "digits_sa": stripped,
            "error_code": None,
        }

    return _invalid("invalid_phone")


# Backward-compatible alias
validate_and_normalize_moroccan_phone = validate_and_normalize_saudi_phone


def _invalid(code: str) -> dict:
    return {
        "is_valid": False,
        "e164": None,
        "digits_sa": None,
        "digits_ma": None,
        "error_code": code,
    }
