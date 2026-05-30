"""Map database connection errors to clear API responses."""

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError, SQLAlchemyError


def raise_if_db_error(exc: Exception) -> None:
    msg = str(exc).lower()
    if (
        isinstance(exc, OperationalError)
        or "connection refused" in msg
        or "connectiondoesnotexist" in msg
        or "1225" in msg
    ):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "database_unavailable",
                "message_ar": "قاعدة البيانات غير متصلة. شغّل PostgreSQL ثم أعد تشغيل الـ API.",
            },
        ) from exc
    if isinstance(exc, SQLAlchemyError):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "database_error",
                "message_ar": "خطأ في قاعدة البيانات. تأكد من تشغيل migration 0002.",
            },
        ) from exc
    raise exc
