"""Simple signed admin session tokens (HMAC)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)


def _secret() -> bytes:
    secret = settings.ADMIN_SESSION_SECRET or settings.HASH_SALT_INTERNAL
    if not secret:
        return b"dev-insecure-admin-secret-change-me"
    return secret.encode("utf-8")


def admin_configured() -> bool:
    return bool(settings.ADMIN_USERNAME and settings.ADMIN_PASSWORD)


def verify_admin_credentials(username: str, password: str) -> bool:
    if not admin_configured():
        return False
    user_ok = secrets.compare_digest(username, settings.ADMIN_USERNAME)
    pass_ok = secrets.compare_digest(password, settings.ADMIN_PASSWORD)
    return user_ok and pass_ok


def create_admin_token(username: str) -> str:
    exp = int(time.time()) + settings.ADMIN_TOKEN_TTL_HOURS * 3600
    payload = json.dumps({"sub": username, "exp": exp}, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    sig = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def decode_admin_token(token: str) -> Optional[str]:
    try:
        payload_b64, sig = token.split(".", 1)
    except ValueError:
        return None
    expected = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
    if not secrets.compare_digest(sig, expected):
        return None
    pad = "=" * (-len(payload_b64) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + pad))
    except (json.JSONDecodeError, ValueError):
        return None
    if payload.get("exp", 0) < int(time.time()):
        return None
    return payload.get("sub")


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if not admin_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "admin_not_configured"},
        )
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized"},
        )
    username = decode_admin_token(credentials.credentials)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token"},
        )
    return username
