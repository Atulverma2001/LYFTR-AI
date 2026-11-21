from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.api import chat, health, sessions
from app.core.config import APP_VERSION, Settings
from app.core.logging import configure_logging
from app.database.connection import create_db_engine, make_session_factory
from app.services.cache_service import init_cache
from app.services.chat_service import ChatService
from app.services.failover_service import FailoverClient

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_cache()
        app.state.settings = settings
        app.state.session_factory = make_session_factory(create_db_engine(settings.database_url))
        app.state.chat_service = ChatService(settings, FailoverClient(settings))
        if len(settings.api_keys) < 2:
            logger.warning("Only %d API key(s) configured; failover needs at least 2", len(settings.api_keys))
        logger.info("Started: %d key(s), simulation=%s", len(settings.api_keys),
                    settings.enable_failure_simulation)
        yield

    app = FastAPI(title="LYFTR AI", version=APP_VERSION, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
        "https://lyftr-ai-chi.vercel.app",
    ],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse({"detail": jsonable_encoder(exc.errors(), custom_encoder={Exception: str})}, status_code=422)

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", type(exc).__name__)
        return JSONResponse({"detail": "internal server error"}, status_code=500)

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(sessions.router)
    return app


app = create_app()
