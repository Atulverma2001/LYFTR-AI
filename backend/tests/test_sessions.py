from tests.conftest import chat, make_client


def test_history_order_and_metadata(client):
    chat(client, "one", session="h")
    chat(client, "two", session="h")
    body = client.get("/sessions/h/messages").json()
    assert body["session_id"] == "h"
    msgs = body["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]
    assert [m["content"] for m in msgs if m["role"] == "user"] == ["one", "two"]
    assert "metadata" not in msgs[0]
    assert set(msgs[1]["metadata"]) >= {"resolution_source", "input_tokens", "output_tokens"}
    assert all(m["role"] != "system" for m in msgs)


def test_unknown_session_404(client):
    r = client.get("/sessions/nope/messages")
    assert r.status_code == 404 and r.json() == {"detail": "session not found"}


def test_history_survives_restart(tmp_path, provider):
    with make_client(tmp_path) as c1:
        chat(c1, "persist me", session="p")
    with make_client(tmp_path) as c2:  # new app instance, same database file
        msgs = c2.get("/sessions/p/messages").json()["messages"]
    assert msgs[0]["content"] == "persist me"


def test_failed_request_not_stored(client, provider):
    provider.failures = {"secret-a": 429, "secret-b": 500}
    assert chat(client, "will fail", session="f").status_code == 503
    assert client.get("/sessions/f/messages").status_code == 404
    provider.failures = {}
    chat(client, "ok now", session="f")
    msgs = client.get("/sessions/f/messages").json()["messages"]
    assert [m["content"] for m in msgs][0] == "ok now" and len(msgs) == 2
