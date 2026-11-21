"""Key-pool failover on top of LiteLLM."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import litellm

from app.core.config import Settings
from app.core.exceptions import AllProvidersUnavailable
from app.schemas.chat import TraceEvent
from app.services.cache_service import is_cache_hit
from app.services.simulation import simulated_status

logger = logging.getLogger(__name__)


@dataclass
class Trace:
    """Ordered list of real events that happened while serving one request."""

    started: float = field(default_factory=time.perf_counter)
    events: list[TraceEvent] = field(default_factory=list)

    def add(self, step: str, detail: str, key_id: str | None = None) -> None:
        elapsed = int((time.perf_counter() - self.started) * 1000)
        self.events.append(TraceEvent(step=step, detail=detail, elapsed_ms=elapsed, key_id=key_id))


@dataclass
class Completion:
    reply: str
    model: str
    input_tokens: int
    output_tokens: int
    key_id: str | None
    fallback_attempts: int
    cache_hit: bool


def _describe(exc: Exception) -> str:
    status = getattr(exc, "status_code", None)
    return str(status) if status else type(exc).__name__


class FailoverClient:
    """Tries each key in order. Any provider failure (429, quota, 5xx, auth, network)
    moves on to the next key; if all fail, AllProvidersUnavailable is raised."""

    def __init__(self, settings: Settings):
        self._settings = settings

    async def complete(
        self,
        messages: list[dict[str, str]],
        simulation: dict[str, int],
        trace: Trace,
    ) -> Completion:
        s = self._settings
        # A simulated request must exercise the live path, so it skips the cache lookup.
        bypass_cache = bool(simulation)
        if bypass_cache:
            trace.add("cache_bypass", "Failure simulation active: cache lookup skipped")
        miss_logged = bypass_cache
        failures = 0

        for key_id, api_key in zip(s.key_ids, s.api_keys):
            status = simulated_status(simulation, key_id)
            if status is not None:
                failures += 1
                trace.add("key_failed", f"{key_id} returned {status} (simulated)", key_id)
                continue

            extra: dict[str, Any] = {"cache": {"no-cache": True}} if bypass_cache else {}
            if s.api_base:
                extra["api_base"] = s.api_base
            try:
                response = await litellm.acompletion(
                    model=s.model,
                    messages=messages,
                    api_key=api_key,
                    timeout=s.request_timeout,
                    num_retries=0,
                    **extra,
                )
            except Exception as exc:  # noqa: BLE001 - every provider failure is failover-eligible
                if not miss_logged:
                    trace.add("cache_miss", "No cached response for this model + messages")
                    miss_logged = True
                failures += 1
                logger.warning("%s failed: %s", key_id, _describe(exc))
                trace.add("key_failed", f"{key_id} returned {_describe(exc)}", key_id)
                continue

            return self._build(response, key_id, failures, trace, miss_logged, messages)

        trace.add("all_failed", f"All {len(s.api_keys)} key(s) failed")
        raise AllProvidersUnavailable()

    def _build(
        self,
        response: Any,
        key_id: str,
        failures: int,
        trace: Trace,
        miss_logged: bool,
        messages: list[dict[str, str]],
    ) -> Completion:
        reply = (response.choices[0].message.content or "").strip()
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "completion_tokens", None)
        if input_tokens is None or output_tokens is None:  # provider gave no usage: estimate
            input_tokens = litellm.token_counter(model=self._settings.model, messages=messages)
            output_tokens = litellm.token_counter(model=self._settings.model, text=reply)

        if is_cache_hit(response):
            trace.add("cache_hit", "Reply served from the LiteLLM cache; no provider call")
            return Completion(reply, self._settings.model, input_tokens, output_tokens, None, 0, True)

        if not miss_logged:
            trace.add("cache_miss", "No cached response for this model + messages")
        if failures:
            trace.add("fallback", f"Fell back after {failures} failed key(s)")
        trace.add("key_succeeded", f"{key_id} answered", key_id)
        return Completion(reply, self._settings.model, input_tokens, output_tokens, key_id, failures, False)
