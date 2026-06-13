import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import (
    attach_trace_id_middleware,
    http_exception_handler,
    rate_limit_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.rate_limit import limiter
from app.core.retention import run_retention_loop
from app.db.session import init_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = init_engine(settings)
    app.state.db_engine = engine
    retention_task: asyncio.Task[None] | None = None
    retention_stop_event: asyncio.Event | None = None

    if settings.auto_create_tables:
        from app.db.base import Base
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine)

    # Fail fast on DB connectivity for non-local environments.
    if settings.environment != "local":
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    if settings.data_retention_enabled:
        retention_stop_event = asyncio.Event()
        retention_task = asyncio.create_task(
            run_retention_loop(retention_stop_event),
            name="data-retention-loop",
        )
        app.state.retention_task = retention_task
        app.state.retention_stop_event = retention_stop_event

    try:
        yield
    finally:
        if retention_stop_event is not None:
            retention_stop_event.set()
        if retention_task is not None:
            await retention_task


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    app.state.limiter = limiter
    app.middleware("http")(attach_trace_id_middleware)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    cors_origins = (
        settings.cors_origins if settings.cors_origins else ["http://localhost:3000"]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SlowAPIMiddleware)
    app.include_router(api_router)
    return app
