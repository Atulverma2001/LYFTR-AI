import pytest

from tests.conftest import chat


@pytest.mark.parametrize("payload", [
    {"session_id": "s", "message": ""},
    {"session_id": "s", "message": "   "},
    {"session_id": "", "message": "hi"},
    {"message": "hi"},
    {"session_id": "s"},
    {"session_id": "s", "message": "x" * 4001},
    {"session_id": "s" * 129, "message": "hi"},
])
def test_invalid_payloads_return_422(client, payload):
    r = client.post("/chat", json=payload)
    assert r.status_code == 422 and "detail" in r.json()


def test_malformed_json_returns_422(client):
    r = client.post("/chat", content="{not json", headers={"content-type": "application/json"})
    assert r.status_code == 422 and "detail" in r.json()


def test_max_length_message_ok_and_trimmed(client):
    assert chat(client, "  " + "x" * 4000 + "  ").status_code == 200


def test_422_not_stored(client):
    client.post("/chat", json={"session_id": "bad", "message": ""})
    assert client.get("/sessions/bad/messages").status_code == 404
