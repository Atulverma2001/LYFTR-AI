from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import ChatSession, Message


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_session(db: Session, session_id: str) -> ChatSession | None:
    return db.get(ChatSession, session_id)


def list_messages(db: Session, session_id: str) -> list[Message]:
    stmt = select(Message).where(Message.session_id == session_id).order_by(Message.id)
    return list(db.scalars(stmt))


def save_exchange(
    db: Session,
    session_id: str,
    system_prompt: str | None,
    user_content: str,
    assistant_content: str,
    assistant_metadata: dict[str, Any],
) -> None:
    """Persist a successful turn atomically: session row, user message, assistant message."""
    now = _now()
    session = db.get(ChatSession, session_id)
    if session is None:
        db.add(ChatSession(session_id=session_id, system_prompt=system_prompt, created_at=now))
    elif system_prompt is not None:
        session.system_prompt = system_prompt
    db.add(Message(session_id=session_id, role="user", content=user_content, created_at=now))
    db.add(
        Message(
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            metadata_json=json.dumps(assistant_metadata),
            created_at=_now(),
        )
    )
    db.commit()
