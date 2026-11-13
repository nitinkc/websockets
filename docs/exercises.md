# Exercises

Hands-on tasks, roughly in order of difficulty.

## 1. Watch a broadcast land

```bash
uv run uvicorn backend.main:app --reload --port 8100
```

Open <http://localhost:8100/events> in **two** tabs and emit
`order.created` from one — the broadcast lands on both, including the
tab that sent it. Watch the client count on the dashboard
(<http://localhost:8100>) drop when you close a tab.

**Question:** why does the emitter receive its own event back? Is that a
bug, or the cheapest acknowledgement protocol there is?

## 2. Reconnect like a real client

Kill the server while a page's socket is open and watch `/events`'s
status chip go dark — it never retries. The ticker page already solves
this: read the `onclose` handler in `ui/ticker.html`, which reconnects
with exponential backoff (1s, doubling, capped at 10s, reset on open)
and re-syncs from the snapshot. Port that to `ui/events.html`.

**Concepts:** websockets give you no delivery guarantee — a socket that
was down during a broadcast simply missed it. How would you catch up?
(An HTTP "get events since X" endpoint is the usual answer — compare
with how a webhook provider retries instead.)

## 3. The slow-client problem

`Hub.broadcast` writes to sockets one at a time. Add a `time.sleep(2)`
to a listener's receive loop (or just never `recv` on one socket), then
broadcast.

**Question:** does one slow socket stall the others? Fix it — send
concurrently with `asyncio.gather`, or give each connection its own
bounded `asyncio.Queue` and a writer task. What does the queue bound
protect you from?

## 4. Auth at the handshake

Right now anyone who can reach the port can join. Add a token check to
`/ws/events`: read `ws.query_params["token"]` (or a header via
`ws.headers`) before `hub.connect`, and `await ws.close(code=4401)` on
mismatch.

**Concepts:** a websocket has one chance to authenticate — the upgrade
request. There's no per-message signature like a webhook delivery; the
handshake IS the auth boundary.

## 5. Heartbeats

A dead client only shows up when a read or write fails — which could be
never. Uvicorn already covers the protocol level: a ping every 20s, and
a client that doesn't pong within 20s is dropped. First watch it work —
start with `--ws-ping-interval 2 --ws-ping-timeout 2`, connect from
Python, and pause the client (`Ctrl+Z`): the server logs the disconnect
seconds later.

Then build the *application*-level version, because ASGI doesn't expose
ping frames to your code: send `{"type": "ping"}` every N seconds from a
task per connection, expect `{"type": "pong"}` back, and drop clients
that go quiet.

**Question:** if the server already pings, why do so many real
protocols add their own app-level heartbeat anyway? (Think: proxies that
terminate the websocket, clients that are alive but wedged, and idle
NATs that drop quiet connections.)

## 6. Rooms

Turn the single `/ws/events` feed into `/ws/events/{room}` — the hub
becomes `dict[str, set[WebSocket]]` and broadcasts only reach the room.

**Concepts:** this is the entire architecture of every chat product.
What in the hub's shape changed, and what stayed identical?

---

Done? Self-check against the [Quiz](quiz.md) — twelve questions,
answers hidden until you ask.
