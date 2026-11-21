"""LiteLLM response cache (LiteLLM's built-in in-memory cache).

LiteLLM derives the cache key from the model and the full message list (plus sampling
parameters, which we leave at their defaults). The session id is never part of the
request sent to LiteLLM, so identical conversations share cache entries across sessions.
"""
from __future__ import annotations

import litellm
from litellm.caching.caching import Cache


def init_cache() -> None:
    litellm.cache = Cache(type="local")


def cache_enabled() -> bool:
    return litellm.cache is not None


def is_cache_hit(response: object) -> bool:
    hidden = getattr(response, "_hidden_params", None) or {}
    return bool(hidden.get("cache_hit"))
