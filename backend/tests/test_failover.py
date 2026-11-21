import pytest

from tests.conftest import chat, make_client


def test_real_429_falls_over_to_key_2(client, provider):
    provider.failures = {"secret-a": 429}
    m = chat(client).json()["metadata"]
    assert m["key_id"] == "key_2" and m["fallback_attempts"] == 1
    assert m["resolution_source"] == "LIVE_INFERENCE"


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_real_provider_statuses_fail_over(client, provider, status):
    provider.failures = {"secret-a": status}
    assert chat(client).json()["metadata"]["key_id"] == "key_2"


def test_quota_error_without_status_fails_over(client, provider):
    provider.failures = {"secret-a": 403}
    assert chat(client).json()["metadata"]["key_id"] == "key_2"


def test_all_real_failures_return_503(client, provider):
    provider.failures = {"secret-a": 429, "secret-b": 500}
    r = chat(client)
    assert r.status_code == 503 and r.json() == {"detail": "all providers unavailable"}


def test_three_keys_two_failures(tmp_path, provider):
    provider.failures = {"k1": 429, "k2": 500}
    with make_client(tmp_path, keys=("k1", "k2", "k3")) as c:
        m = chat(c).json()["metadata"]
    assert m["key_id"] == "key_3" and m["fallback_attempts"] == 2


# --- X-Simulate-Failure -------------------------------------------------------------

@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_simulated_status_uses_key_2(client, provider, status):
    r = chat(client, headers={"X-Simulate-Failure": f"key_1={status}"})
    assert r.status_code == 200
    assert r.json()["metadata"]["key_id"] == "key_2" and r.json()["metadata"]["fallback_attempts"] == 1
    assert all(c["api_key"] == "secret-b" for c in provider.calls)  # key_1 never really called


def test_simulation_trace_is_real(client):
    steps = [(e["step"], e["key_id"]) for e in chat(client, headers={"X-Simulate-Failure": "key_1=429"}).json()["trace"]]
    assert ("key_failed", "key_1") in steps and ("key_succeeded", "key_2") in steps and ("fallback", None) in steps


def test_wildcard_returns_503_and_stores_nothing(client):
    r = chat(client, session="w", headers={"X-Simulate-Failure": "*=429"})
    assert r.status_code == 503 and r.json() == {"detail": "all providers unavailable"}
    assert client.get("/sessions/w/messages").status_code == 404


def test_multiple_simulated_keys_503(client):
    assert chat(client, headers={"X-Simulate-Failure": "key_1=429,key_2=500"}).status_code == 503


def test_simulation_bypasses_cache_so_failover_is_demonstrable(client):
    chat(client, "cached question")  # populates the cache
    r = chat(client, "cached question", session="z", headers={"X-Simulate-Failure": "key_1=429"}).json()
    assert r["metadata"]["resolution_source"] == "LIVE_INFERENCE" and r["metadata"]["key_id"] == "key_2"
    assert chat(client, "cached question", session="y", headers={"X-Simulate-Failure": "*=429"}).status_code == 503


def test_simulation_ignored_when_disabled(tmp_path, provider):
    with make_client(tmp_path, simulation=False) as c:
        r = chat(c, headers={"X-Simulate-Failure": "*=429"})
    assert r.status_code == 200 and r.json()["metadata"]["key_id"] == "key_1"


def test_bad_header_is_422(client):
    assert chat(client, headers={"X-Simulate-Failure": "key_1=418"}).status_code == 422
    assert chat(client, headers={"X-Simulate-Failure": "garbage"}).status_code == 422
