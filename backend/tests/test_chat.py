from tests.conftest import chat


def test_contract_fields(client, provider):
    r = chat(client)
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == "s-1"
    assert body["reply"]
    m = body["metadata"]
    assert set(m) == {"resolution_source", "model", "latency_ms", "input_tokens", "output_tokens",
                      "key_id", "fallback_attempts"}
    assert m["resolution_source"] == "LIVE_INFERENCE"
    assert m["key_id"] == "key_1" and m["fallback_attempts"] == 0
    assert isinstance(m["latency_ms"], int) and m["input_tokens"] > 0 and m["output_tokens"] > 0
    assert "secret" not in r.text


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["keys_configured"] == 2 and body["cache_enabled"] is True


def test_multi_turn_sends_history_to_llm(client, provider):
    chat(client, "What is machine learning?")
    chat(client, "Give me three applications.")
    sent = provider.calls[-1]["messages"]
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"]
    assert sent[1]["content"] == "What is machine learning?"
    assert sent[-1]["content"] == "Give me three applications."


def test_sessions_are_isolated(client, provider):
    chat(client, "Remember: blue", session="a")
    chat(client, "Hello", session="b")
    sent = provider.calls[-1]["messages"]
    assert len(sent) == 2  # system + the new message only


def test_system_prompt_overrides_and_persists_for_session(client, provider):
    chat(client, "hi", system_prompt="Answer like a pirate.")
    assert provider.calls[-1]["messages"][0]["content"] == "Answer like a pirate."
    chat(client, "again")  # prompt remembered for the session
    assert provider.calls[-1]["messages"][0]["content"] == "Answer like a pirate."


def test_tokens_are_provider_usage_per_request_not_running_total(client):
    # LiteLLM's mock provider always reports 10 prompt / 20 completion tokens, so a running
    # total would show up as growth across turns.
    for text in ("one", "two", "three"):
        m = chat(client, text, session="t").json()["metadata"]
        assert (m["input_tokens"], m["output_tokens"]) == (10, 20)


def test_token_estimate_when_provider_reports_no_usage():
    from types import SimpleNamespace

    from app.core.config import Settings
    from app.services.failover_service import FailoverClient, Trace

    resp = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Paris"))], usage=None, _hidden_params={}
    )
    client = FailoverClient(Settings(api_keys=("a",)))
    out = client._build(resp, "key_1", 0, Trace(), False, [{"role": "user", "content": "Capital of France?"}])
    assert out.input_tokens > 0 and out.output_tokens > 0
