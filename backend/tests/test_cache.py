from tests.conftest import chat


def test_identical_request_in_new_session_hits_cache(client, provider):
    first = chat(client, "What is the capital of France?", session="one").json()
    second = chat(client, "What is the capital of France?", session="two").json()
    assert first["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    m = second["metadata"]
    assert m["resolution_source"] == "LLM_CACHE"
    assert second["reply"] == first["reply"]  # provider would have said answer-2
    assert m["key_id"] is None and m["fallback_attempts"] == 0
    assert m["input_tokens"] == first["metadata"]["input_tokens"]
    assert m["output_tokens"] == first["metadata"]["output_tokens"]
    assert [e["step"] for e in second["trace"]] == ["request_received", "cache_hit", "response_returned"]


def test_different_message_misses(client):
    chat(client, "Question A", session="a")
    r = chat(client, "Question B", session="b").json()
    assert r["metadata"]["resolution_source"] == "LIVE_INFERENCE" and r["reply"] == "answer-2"


def test_different_system_prompt_misses(client):
    chat(client, "Same question", session="a", system_prompt="Be brief.")
    r = chat(client, "Same question", session="b", system_prompt="Be verbose.").json()
    assert r["metadata"]["resolution_source"] == "LIVE_INFERENCE"


def test_different_history_misses(client):
    chat(client, "Hello", session="a")
    chat(client, "Follow up", session="a")  # history: Hello/answer-1
    chat(client, "Something else", session="b")
    r = chat(client, "Follow up", session="b").json()  # history differs from session a
    assert r["metadata"]["resolution_source"] == "LIVE_INFERENCE"


def test_cache_miss_trace_on_live(client):
    steps = [e["step"] for e in chat(client, "fresh").json()["trace"]]
    assert steps == ["request_received", "cache_miss", "key_succeeded", "response_returned"]
