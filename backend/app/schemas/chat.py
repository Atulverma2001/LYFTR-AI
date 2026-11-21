from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str
    system_prompt: str | None = Field(default=None, max_length=4000)

    @field_validator("message")
    @classmethod
    def _message_length(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= 4000:
            raise ValueError("message must be 1-4000 characters after trimming whitespace")
        return value

    @field_validator("system_prompt")
    @classmethod
    def _blank_prompt_is_none(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class ChatMetadata(BaseModel):
    resolution_source: Literal["LIVE_INFERENCE", "LLM_CACHE"]
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    key_id: str | None
    fallback_attempts: int


class TraceEvent(BaseModel):
    step: str
    detail: str
    elapsed_ms: int
    key_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    metadata: ChatMetadata
    trace: list[TraceEvent] = []  # extra field: real backend events for this request
