# Lyftr AI

*Reliable AI. Intelligent Infrastructure. Transparent Performance.*

A multi-turn LLM chatbot (React + FastAPI + LiteLLM + SQLite) with automatic API-key failover, LiteLLM response caching, per-request token/latency metadata, and a built-in way to demonstrate failover on demand.

## 1. Live URLs

| | URL |
|---|---|
| Frontend | **Pending: not deployed yet** |
| Backend | **Pending: not deployed yet** |

Deployment notes are at the end of this file. Set `ENABLE_FAILURE_SIMULATION=true` on the deployed backend.

## 2. Run locally: with Docker and without

### With Docker (requires Docker + Compose + make)

```bash
cp .env.example .env     # then put at least two real keys in LLM_API_KEYS
make up                  # frontend http://localhost:3000, backend http://localhost:8000
make down                # stop; the SQLite volume is kept
```

The database is `/data/app.db` on the named volume `lyftr_data`, so history survives `make down` / `make up` and container restarts. (`docker compose down -v` deletes it.)

### Without Docker (Python 3.12, Node 20+)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export LLM_API_KEYS=key-one,key-two DATABASE_URL=sqlite:///./app.db \
       ALLOWED_ORIGINS=http://localhost:3000 ENABLE_FAILURE_SIMULATION=true
uvicorn app.main:app --port 8000          # schema is created on startup

# Frontend (second terminal)
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev    # http://localhost:3000
```

### Environment variables

| Variable | Meaning |
|---|---|
| `LLM_API_KEYS` | Comma-separated key pool, ids `key_1`, `key_2`, … in order |
| `LLM_MODEL` | LiteLLM model name (default `gemini/gemini-2.0-flash`); keys must match its provider |
| `LLM_API_BASE` | Optional OpenAI-compatible endpoint override |
| `DATABASE_URL` | e.g. `sqlite:////data/app.db` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `ENABLE_FAILURE_SIMULATION` | `true` enables the `X-Simulate-Failure` header |
| `LLM_TIMEOUT_SECONDS`, `MAX_HISTORY_MESSAGES` | Per-attempt timeout (30), history messages sent to the model (50) |
| `VITE_API_URL` | Frontend build-time backend URL, as seen by the browser |

### Tests

```bash
make test-backend     # 44 pytest tests, no API keys needed
make test-frontend    # vitest
```

## 3. Design decisions: key fallback, caching, SQLite session storage

**Key fallback.** `FailoverClient` walks the key pool in order and calls `litellm.acompletion` with one key per attempt, with LiteLLM's own retries disabled so failover is ours and visible. Any provider failure (429, quota, 5xx, auth, timeout, network) moves to the next key. Success returns `key_id` (`key_1`…, never the secret) and `fallback_attempts` (failed keys before success). If every key fails the API returns `503 {"detail": "all providers unavailable"}` and nothing is stored. Keys are never logged or returned; only ids appear.

**Failure simulation.** With `ENABLE_FAILURE_SIMULATION=true`, `X-Simulate-Failure: key_1=429,key_2=500` or `*=429` makes the listed keys fail inside that one request, before the provider call, through the same loop as real failures. Statuses: 429, 500, 502, 503. Specific keys beat `*`. A malformed header is a 422. When the switch is off the header is ignored. Design choice: a simulated request skips the cache lookup, otherwise a previously cached question could never demonstrate failover or the `*=429` → 503 case.

**Caching.** LiteLLM's built-in in-memory cache (`litellm.cache = Cache(type="local")`). The cache key is LiteLLM's hash of the model plus the full message list (system prompt + history + new message). The session id is never part of the LLM call, so the same first message in a new session hits the cache, while a different message, system prompt or history cannot. Hits are detected from LiteLLM's `cache_hit` flag, reported as `LLM_CACHE` with `key_id: null`, `fallback_attempts: 0`, and the usage stored with the cached response. Limitation: the cache is in-memory (the LiteLLM version pinned here removed its disk backend), so it is emptied on restart; SQLite history is not.

**SQLite session storage.** Tables: `messages` (exact schema from the assignment, plus an index) and `sessions` (stores the per-session system prompt, which is therefore excluded from the history endpoint). A turn is written in one transaction only after the LLM succeeds, so 422/503 requests never touch history. A per-session lock keeps concurrent turns from interleaving. The client sends only the new message; the backend rebuilds `system + history + new message`.

**Tokens and latency.** Tokens come from the provider usage that LiteLLM returns (per request, never a running total); if a provider returns none, LiteLLM's token counter provides an estimate. Latency is measured server-side with a monotonic clock.

**Structure:** `backend/app/{api,core,database,schemas,services}`, `frontend/src/{components,api.ts,types.ts}`.

## 4. Verification: how to see failover, cache hits and per-message token usage

Use the UI (or curl at `http://localhost:8000`). Every assistant reply shows source, model, latency, input and output tokens.

1. **Live inference.** Send "What is the capital of France?" → `LIVE_INFERENCE`, `key_1`.
2. **Cache hit.** Click **New chat**, send the identical message → `LLM_CACHE`, same reply and tokens, lower latency, `key_id` null.
3. **Cache miss.** Change one word, or set a different system prompt → `LIVE_INFERENCE`.
4. **Failover.** In the chat, choose "key_1 returns 429" in the failure dropdown (visible when simulation is on) and send → answered by `key_2`, 1 fallback.
   ```bash
   curl -s localhost:8000/chat -H 'content-type: application/json' -H 'X-Simulate-Failure: key_1=429' \
     -d '{"session_id":"demo","message":"hello"}'      # 200, key_id key_2, fallback_attempts 1
   curl -s -i localhost:8000/chat -H 'content-type: application/json' -H 'X-Simulate-Failure: *=429' \
     -d '{"session_id":"demo2","message":"hello"}'     # 503 {"detail":"all providers unavailable"}
   curl -s localhost:8000/sessions/demo2/messages      # 404: the failed request was not stored
   ```
5. **Per-message tokens.** Ask a follow-up in the same chat: input tokens grow (history is included) while each reply reports only its own request.
6. **Multi-turn and history.** Tell the bot your name, then ask for it. `GET /sessions/{id}/messages` returns oldest-first messages with assistant metadata, no system prompt. Restart the stack and fetch it again.
7. **Errors.** An over-long or empty message → 422 shown in chat; `curl` malformed JSON → 422 JSON.
8. **Playground tab.** One-click experiments for all of the above, each sending real requests and showing the response and trace.

## 5. Setup Used: your editor and AI tools

- AI tool: Claude (Anthropic) generated and iterated on this codebase, running the tests in a sandbox.
- Editor: *fill in your own editor before submitting.*

## 6. Bonus features (if any): what you added beyond the requirements and why

- **Request insights panel.** Shows the last request's metadata plus a trace of events the backend recorded (cache lookup, per-key failures, fallback, success). It explains *why* a reply came from where it did.
- **Developer playground.** Guided experiments for cache, system-prompt cache misses, memory, failover and 503/422, so evaluators needn't hand-craft headers.
- **System diagnostics.** Live view of `/health` (database, cache, model, key count, simulation flag, version). Unknown values show as unknown.
- **System-prompt field** with the required `system-prompt-input` test id, markdown/code rendering and copy buttons.

The API also returns an extra top-level `trace` array and extra `/health` fields; the contract allows extra fields.

## API summary

`GET /health` · `POST /chat` (`session_id`, `message`, optional `system_prompt`; optional `X-Simulate-Failure`) · `GET /sessions/{session_id}/messages`. Errors are always JSON `{"detail": ...}`: 422 validation, 404 unknown session, 503 all keys failed.

## Security

Keys live only in environment variables, are never returned, logged or baked into images; `.env` is git-ignored. CORS is limited to `ALLOWED_ORIGINS`. Inputs are validated with Pydantic and unhandled errors return a generic JSON 500 without stack traces. The backend container runs as a non-root user.

## Deployment notes

- **Backend** (Render, Railway, Fly.io): deploy `backend/` with its Dockerfile; set the env vars above and `ALLOWED_ORIGINS` to the frontend URL. SQLite needs a persistent disk/volume mounted at `/data` (Render: paid disk; Fly: a volume); without one, history resets on redeploy. Run a single instance only.
- **Frontend** (Vercel, Netlify, Cloudflare Pages, or the Dockerfile): build with `VITE_API_URL` set to the public backend URL.
