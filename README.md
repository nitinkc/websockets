# websockets-101

A minimal playground for learning **WebSockets** — server push over one
long-lived connection. The same toy flow (*something happened → tell
interested parties*) with the simplest possible transport:

- **`WS /ws/echo`** — text comes back prefixed with `echo: `; binary
  frames come back unchanged. The raw send/receive loop.
- **`WS /ws/events`** — the live feed. Connect to subscribe; send
  `{"type": ..., "data": {...}}` on the socket to emit an event, which is
  broadcast to every connected client — the socket works *both* ways.
- **`WS /ws/ticker`** — a fake market-data feed. The server is the
  exchange: a random walk ticks once a second and is pushed to every
  connected client. Pure server push — connecting is subscribing.

No accounts, no credentials, no per-message HTTP. Everything runs locally.

> This repo is one of three sibling playgrounds. The webhook version lives
> in `../webhooks` (signed `POST`s with retries); the gRPC version in
> `../grpc-101` (typed streams with a `.proto` contract).

## Quickstart

```bash
uv sync
uv run uvicorn backend.main:app --reload --port 8100   # app  → http://localhost:8100
uv run mkdocs serve                                # docs → http://127.0.0.1:8000
uv run pytest                                      # tests
```

The docs run on **8000** (`dev_addr` in `mkdocs.yml`) and the app on
**8100**, so both can be up at once. Uvicorn defaults to 8000, so always
pass `--port 8100` — without it the app collides with the docs. To move
the app elsewhere, change the port — every page derives its socket URL
from `location.origin`, so nothing else needs to change.

Without uv: `requirements.txt` is a `uv export` of the full lockfile
(runtime + dev), so `pip install -r requirements.txt` in any venv gives
you the same set.

## Routes

| Route | Kind | What it is |
| --- | --- | --- |
| `/` | page | dashboard — polls `/api/events` every 2s |
| `/echo`, `/events`, `/ticker` | page | one interactive playground per socket |
| `/ws/echo`, `/ws/events`, `/ws/ticker` | WebSocket | the three sockets above |
| `/api/events` | GET | last 30 events (newest first) + client count on `/ws/events` |
| `/health` | GET | `{"status": "ok"}` |
| `/docs`, `/redoc` | GET | FastAPI's generated API reference (HTTP routes only) |
