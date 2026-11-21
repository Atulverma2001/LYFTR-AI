"""Runtime configuration, read once from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass

APP_VERSION = "1.0.0"
DEFAULT_SYSTEM_PROMPT = "You are a helpful, concise assistant."


def _split(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    api_keys: tuple[str, ...]
    database_url: str = "sqlite:////data/app.db"
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    enable_failure_simulation: bool = False
    model: str = "gemini/gemini-2.0-flash"
    api_base: str | None = None  # optional OpenAI-compatible endpoint override
    request_timeout: float = 30.0
    max_history_messages: int = 50
    default_system_prompt: str = DEFAULT_SYSTEM_PROMPT

    @property
    def key_ids(self) -> tuple[str, ...]:
        """Public identifiers (key_1, key_2, ...) in pool order. Never the secrets."""
        return tuple(f"key_{i}" for i in range(1, len(self.api_keys) + 1))

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ.get
        return cls(
            api_keys=_split(env("LLM_API_KEYS", "")),
            database_url=env("DATABASE_URL", cls.database_url),
            allowed_origins=_split(env("ALLOWED_ORIGINS", "http://localhost:3000")),
            enable_failure_simulation=env("ENABLE_FAILURE_SIMULATION", "false").lower() == "true",
            model=env("LLM_MODEL", cls.model),
            api_base=env("LLM_API_BASE") or None,
            request_timeout=float(env("LLM_TIMEOUT_SECONDS", str(cls.request_timeout))),
            max_history_messages=int(env("MAX_HISTORY_MESSAGES", str(cls.max_history_messages))),
            default_system_prompt=env("DEFAULT_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT),
        )
