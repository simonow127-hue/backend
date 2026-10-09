from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    APP_NAME: str = "riads-api"
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://localhost:3001,"
        "http://localhost:3004,"
        "http://127.0.0.1:3000,"
        "http://127.0.0.1:3001,"
        "http://127.0.0.1:3004"
    )

    DATABASE_URL: str = (
        "postgresql+asyncpg://riads:riads@localhost:5432/riads"
    )

    RUN_MIGRATIONS_ON_START: bool = False

    # ============================================================
    # GOOGLE SHEETS
    # ============================================================

    GOOGLE_SHEETS_WEBHOOK_URL: str = ""

    GOOGLE_SHEETS_SPREADSHEET_ID: str = (
        "1noCh6q_Q-G-fnFWUoPdiHJ7aVL-9r2BMdHTI2xrVl1I"
    )

    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""
    GOOGLE_SERVICE_ACCOUNT_JSON_B64: str = ""

    # ============================================================
    # META
    # ============================================================

    META_PIXEL_ID: str = ""
    META_ACCESS_TOKEN: str = ""
    META_TEST_EVENT_CODE: str = ""

    # ============================================================
    # TIKTOK
    # ============================================================

    TIKTOK_PIXEL_ID: str = ""
    TIKTOK_ACCESS_TOKEN: str = ""
    TIKTOK_TEST_EVENT_CODE: str = ""

    # ============================================================
    # SNAPCHAT
    # ============================================================

    SNAP_PIXEL_ID: str = ""
    SNAP_ACCESS_TOKEN: str = ""

    # ============================================================
    # INTERNAL
    # ============================================================

    HASH_SALT_INTERNAL: str = ""

    ENABLE_CAPI: bool = True
    ENABLE_SHEETS_WEBHOOK: bool = True

    LOG_LEVEL: str = "INFO"

    # ============================================================
    # MAXMIND GEOIP2
    # ============================================================

    MAXMIND_ACCOUNT_ID: str = ""
    MAXMIND_LICENSE_KEY: str = ""

    ENABLE_GEO_RESTRICTION: bool = True

    # Supported order countries:
    # SA = Saudi Arabia
    # AE = United Arab Emirates
    ALLOWED_COUNTRIES: str = "SA,AE"

    BLOCK_VPN: bool = True
    BLOCK_TOR: bool = True
    BLOCK_HOSTING: bool = True

    # If MaxMind is unreachable:
    # True  = allow order
    # False = block order
    GEO_FAIL_OPEN: bool = True

    # ============================================================
    # IPQUALITYSCORE
    # ============================================================

    IPQS_API_KEY: str = ""
    IPQS_STRICTNESS: int = 1

    # ============================================================
    # ADMIN DASHBOARD
    # ============================================================

    ADMIN_USERNAME: str = ""
    ADMIN_PASSWORD: str = ""
    ADMIN_SESSION_SECRET: str = ""
    ADMIN_TOKEN_TTL_HOURS: int = 24

    # ============================================================
    # HELPERS
    # ============================================================

    @property
    def cors_origins_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def allowed_countries_list(self) -> List[str]:
        return [
            country.strip().upper()
            for country in self.ALLOWED_COUNTRIES.split(",")
            if country.strip()
        ]

    @property
    def db_url_async(self) -> str:
        url = self.DATABASE_URL

        if url.startswith("postgres://"):
            url = (
                "postgresql+asyncpg://"
                + url[len("postgres://"):]
            )
        elif url.startswith("postgresql://"):
            url = (
                "postgresql+asyncpg://"
                + url[len("postgresql://"):]
            )

        if "?sslmode=" in url:
            url = url.split("?sslmode=")[0]

        return url

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


settings = Settings()
