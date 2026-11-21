"""Orchestrates one chat turn: load history, call the LLM, persist on success."""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database import repository
from app.schemas.chat import ChatMetadata, ChatRequest, ChatResponse
from app.services.failover_service import FailoverClient, Trace


class ChatService:
    def __init__(self, settings: Settings, client: FailoverClient):
        self._settings = settings
        self._client = client
        # Serialise turns within one session so history is never interleaved.
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def chat(self, db: Session, req: ChatRequest, simulation: dict[str, int]) -> ChatResponse:
        started = time.perf_counter()
        trace = Trace(started=started)
        trace.add("request_received", f"session {req.session_id}")

        async with self._locks[req.session_id]:
            session = repository.get_session(db, req.session_id)
            system_prompt = req.system_prompt or (session.system_prompt if session else None)
            history = repository.list_messages(db, req.session_id)[-self._settings.max_history_messages :]

            messages = [{"role": "system", "content": system_prompt or self._settings.default_system_prompt}]
            messages += [{"role": m.role, "content": m.content} for m in history]
            messages.append({"role": "user", "content": req.message})

            completion = await self._client.complete(messages, simulation, trace)

            metadata = ChatMetadata(
                resolution_source="LLM_CACHE" if completion.cache_hit else "LIVE_INFERENCE",
                model=completion.model,
                latency_ms=int((time.perf_counter() - started) * 1000),
                input_tokens=completion.input_tokens,
                output_tokens=completion.output_tokens,
                key_id=completion.key_id,
                fallback_attempts=completion.fallback_attempts,
            )
            repository.save_exchange(
                db,
                req.session_id,
                req.system_prompt,
                req.message,
                completion.reply,
                metadata.model_dump(),
            )
        trace.add("response_returned", "Saved to session history")
        return ChatResponse(
            session_id=req.session_id, reply=completion.reply, metadata=metadata, trace=trace.events
        )
