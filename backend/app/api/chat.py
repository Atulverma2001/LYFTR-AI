from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import AllProvidersUnavailable, InvalidSimulationHeader
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.simulation import parse_simulation_header

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    x_simulate_failure: str | None = Header(default=None),
) -> ChatResponse:
    simulation: dict[str, int] = {}
    if request.app.state.settings.enable_failure_simulation:
        try:
            simulation = parse_simulation_header(x_simulate_failure)
        except InvalidSimulationHeader as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        return await request.app.state.chat_service.chat(db, body, simulation)
    except AllProvidersUnavailable as exc:
        raise HTTPException(status_code=503, detail="all providers unavailable") from exc
