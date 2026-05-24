import hashlib


def sha256_hex(value: str) -> str:
    """Hash a string with SHA-256 and return lowercase hex."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_phone_meta_snap(phone_digits_ma: str) -> str:
    """Hash phone for Meta/Snap CAPI: digits with country code, no +."""
    return sha256_hex(phone_digits_ma)


def hash_phone_tiktok(phone_e164: str) -> str:
    """Hash phone for TikTok CAPI: E.164 with + prefix."""
    return sha256_hex(phone_e164)
