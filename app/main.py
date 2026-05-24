import logging
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import health, orders, analytics

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("riads.main")


def run_migrations() -> None:
    logger.info("Running Alembic migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Migration failed:\n%s\n%s", result.stdout, result.stderr)
        if settings.is_production:
            raise RuntimeError("Database migration failed — aborting startup.")
        else:
            logger.warning("Migration failed in non-production; continuing anyway.")
    else:
        logger.info("Migrations complete.\n%s", result.stdout)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.RUN_MIGRATIONS_ON_START:
        run_migrations()
    yield


app = FastAPI(
    title="Riads API",
    description="Backend for Riads.shop — Moroccan premium DTC COD beauty store.",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(orders.router)
app.include_router(analytics.router)
