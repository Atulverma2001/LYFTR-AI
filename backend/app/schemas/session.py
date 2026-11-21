from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class StoredMessage(BaseModel):
    role: str
    content: str
    metadata: dict[str, Any] | None = None


class SessionMessages(BaseModel):
    session_id: str
    messages: list[StoredMessage]
