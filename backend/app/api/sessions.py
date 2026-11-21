from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.database import repository
from app.schemas.session import SessionMessages, StoredMessage

router = APIRouter()


@router.get("/sessions/{session_id}/messages", response_model=SessionMessages, response_model_exclude_none=True)
def session_messages(session_id: str, db: Session = Depends(get_db)) -> SessionMessages:
    if repository.get_session(db, session_id) is None:
        raise HTTPException(status_code=404, detail="session not found")
    messages = [
        StoredMessage(
            role=m.role,
            content=m.content,
            metadata=json.loads(m.metadata_json) if m.metadata_json else None,
        )
        for m in repository.list_messages(db, session_id)
    ]
    return SessionMessages(session_id=session_id, messages=messages)
