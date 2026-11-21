from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import APP_VERSION
from app.services.cache_service import cache_enabled

router = APIRouter()


@router.get("/health")
def health(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    try:
        with request.app.state.session_factory() as db:
            db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001
        database = "unreachable"
    keys = len(settings.api_keys)
    healthy = database == "ok" and keys > 0
    body = {
        "status": "ok" if healthy else "degraded",
        "keys_configured": keys,
        "cache_enabled": cache_enabled(),
        # Extra fields (allowed by the contract) used by the Diagnostics view.
        "database": database,
        "model": settings.model,
        "cache_type": "in-memory",
        "failure_simulation_enabled": settings.enable_failure_simulation,
        "version": APP_VERSION,
    }
    return JSONResponse(body, status_code=200 if healthy else 503)
