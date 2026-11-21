"""Test harness.

LiteLLM's real acompletion is kept (so its real cache runs) but every call is given a
`mock_response`, so no network or API key is needed. A cache hit returns the *first*
reply text, which is how tests prove that the provider was not asked again.
"""
from __future__ import annotations

import itertools

import litellm
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class FakeProvider:
    def __init__(self) -> None:
        self.counter = itertools.count(1)
        self.calls: list[dict] = []  # one entry per call that reached litellm
        self.failures: dict[str, int] = {}  # api_key -> HTTP status to raise
        self.original = litellm.acompletion

    async def __call__(self, **kwargs):
        self.calls.append(kwargs)
        status = self.failures.get(kwargs["api_key"])
        if status:
            err = RuntimeError(f"provider error {status}")
            err.status_code = status  # type: ignore[attr-defined]
            raise err
        kwargs.pop("timeout", None)
        return await self.original(mock_response=f"answer-{next(self.counter)}", **kwargs)


@pytest.fixture
def provider(monkeypatch) -> FakeProvider:
    fake = FakeProvider()
    monkeypatch.setattr(litellm, "acompletion", fake)
    return fake


def make_client(tmp_path, simulation: bool = True, keys=("secret-a", "secret-b")) -> TestClient:
    settings = Settings(
        api_keys=tuple(keys),
        database_url=f"sqlite:///{tmp_path}/test.db",
        enable_failure_simulation=simulation,
        model="gemini/gemini-2.0-flash",
    )
    return TestClient(create_app(settings))


@pytest.fixture
def client(tmp_path, provider):
    with make_client(tmp_path) as c:
        yield c


def chat(client, message="What is the capital of France?", session="s-1", headers=None, **extra):
    return client.post("/chat", json={"session_id": session, "message": message, **extra}, headers=headers or {})
