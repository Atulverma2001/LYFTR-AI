"""Parser for the X-Simulate-Failure header."""
from __future__ import annotations

from app.core.exceptions import InvalidSimulationHeader

ALLOWED_STATUSES = {429, 500, 502, 503}


def parse_simulation_header(header: str | None) -> dict[str, int]:
    """'key_1=429,key_2=500' -> {'key_1': 429, 'key_2': 500}. '*' matches every key."""
    if not header or not header.strip():
        return {}
    rules: dict[str, int] = {}
    for pair in header.split(","):
        target, sep, status_text = pair.strip().partition("=")
        target, status_text = target.strip(), status_text.strip()
        if not sep or not target or not status_text.isdigit() or int(status_text) not in ALLOWED_STATUSES:
            raise InvalidSimulationHeader(
                "X-Simulate-Failure must look like 'key_1=429,key_2=500' or '*=429' "
                f"(statuses: {sorted(ALLOWED_STATUSES)})"
            )
        rules[target] = int(status_text)
    return rules


def simulated_status(rules: dict[str, int], key_id: str) -> int | None:
    """Specific key rules win over the '*' wildcard."""
    return rules.get(key_id, rules.get("*"))
