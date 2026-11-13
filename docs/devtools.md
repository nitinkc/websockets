# Watching websockets in Chrome DevTools

A websocket is almost invisible in the Network tab — one request, then
silence. This page shows where it hides and how to watch the frames.

## The one thing that trips everyone up

**DevTools only records traffic while it's open.** The playground pages
(`<host>/echo`, `/events`, `/ticker`) connect the moment they load, so if
you opened the page *then* opened DevTools, the handshake already
happened and the Network tab looks empty.

Fix: open DevTools first, then reload. On `/echo` and `/events` you can
also use the **disconnect / connect** button, which forces a fresh
handshake while DevTools is watching. `/ticker` has no button — it
reconnects on its own, so reload it (or restart the server and watch it
come back).

## Finding the socket

1. `F12` → **Network** tab.
2. Click the **WS** filter chip (next to Fetch/XHR, JS, CSS…). The
   socket doesn't appear under Fetch/XHR or Doc — a websocket is *not*
   an XHR.
3. Reconnect (button on the page, or reload). One row appears:

   | Name | Status |
   | --- | --- |
   | `ws/echo` | `101 Switching Protocols` |

That single `GET` **is** the websocket: it started as an HTTP request
with `Upgrade: websocket`, the server agreed with `101`, and the TCP
connection became a pipe. After it, **no new requests appear, ever** —
everything else is frames inside that one connection.

## Watching the frames

Click the row → **Messages** tab.

- **Green/up** = frame you sent, **red/down** = frame the server pushed.
- Try it on `/echo`: type in the send box, see a green frame and an
  immediate red reply — one pair per message.
- On `/events`: emit an event with a second tab connected; the same
  broadcast frame lands in **both** tabs' Messages views.
- On `/ticker`: a red `{"type":"tick",…}` frame arrives every second
  with nothing green in between — pure server push.
- What you **won't** see: ping/pong. Uvicorn sends a protocol-level
  ping (opcode 9) every 20s and the browser answers with a pong
  (opcode 10), but Chrome doesn't list control frames in Messages — the
  heartbeat is real, just invisible here. Wireshark on `lo0` shows it.

The **Headers** tab on the same row is worth a look too: it shows the
request that opened the pipe (`Upgrade: websocket`,
`Sec-WebSocket-Key: …`, `Sec-WebSocket-Version: 13`) — the same headers
you'd send by hand with `websocat` or the `websockets` library.

## What the Messages tab tells you about real systems

- **Frame count vs. message count.** Every send is a frame — no batching,
  no headers, ~2 bytes of overhead. Compare with the Network tab's
  waterfall on a polling page: each event there is a whole request.
- **Who talks.** Only green on `/events` when *you* emit; only red on
  `/ticker`. The direction split is the architecture, made visible.
- **Death.** Kill the server (`Ctrl+C` on uvicorn) and the Messages tab
  ends — the row doesn't get a "failed" status, the connection just
  stops. Reconnect on the page and a *new* WS row appears; the old one
  is history. On `/ticker` you'll watch this happen by itself: failed
  rows pile up at 1s, 2s, 4s… (capped at 10s) until the server is back.
  That's the "socket closes; client reconnects" failure model from the
  guide.

## `wss` in DevTools

Identical — same row, same Messages tab. The only visible difference is
the scheme in the URL and, in Headers, that the whole handshake ran over
TLS. DevTools can still see the frames because it sits *inside* the
encryption, not on the wire.
