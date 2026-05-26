from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

    DATABASE_URL: str = "postgresql+asyncpg://riads:riads@localhost:5432/riads"
    RUN_MIGRATIONS_ON_START: bool = False

    GOOGLE_SHEETS_WEBHOOK_URL: str = ""
    GOOGLE_SHEETS_SPREADSHEET_ID: str = "1Dypu_WkwyH2VXI94nOg4urxby20ktNMu2Od5wulRvRs"
    # Option A (recommended): service account JSON — share the sheet with client_email as Editor
    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""
    GOOGLE_SERVICE_ACCOUNT_JSON_B64: str = ""

    META_PIXEL_ID: str = ""
    META_ACCESS_TOKEN: str = ""
    META_TEST_EVENT_CODE: str = ""

    TIKTOK_PIXEL_ID: str = ""
    TIKTOK_ACCESS_TOKEN: str = ""
    TIKTOK_TEST_EVENT_CODE: str = ""

    SNAP_PIXEL_ID: str = ""
    SNAP_ACCESS_TOKEN: str = ""

    HASH_SALT_INTERNAL: str = ""
    ENABLE_CAPI: bool = True
    ENABLE_SHEETS_WEBHOOK: bool = True
    LOG_LEVEL: str = "INFO"

    # MaxMind GeoIP2 Insights — order fraud/geo guard
    MAXMIND_ACCOUNT_ID: str = ""
    MAXMIND_LICENSE_KEY: str = ""
    ENABLE_GEO_RESTRICTION: bool = True
    ALLOWED_COUNTRIES: str = "MA"
    BLOCK_VPN: bool = True
    BLOCK_TOR: bool = True
    BLOCK_HOSTING: bool = True
    GEO_FAIL_OPEN: bool = True  # if MaxMind unreachable, allow order (set False to block)

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_countries_list(self) -> List[str]:
        return [c.strip().upper() for c in self.ALLOWED_COUNTRIES.split(",") if c.strip()]

    @property
    def db_url_async(self) -> str:
        url = self.DATABASE_URL
        # Convert postgres:// -> postgresql+asyncpg://
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        # Remove sslmode param for asyncpg (handled separately)
        if "?sslmode=" in url:
            url = url.split("?sslmode=")[0]
        return url

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
