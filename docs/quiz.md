# Quiz

Twelve questions on the concepts — single answer, select-all, and a few
fill-in-the-blank. Explanations appear after each answer.

<!-- mkdocs-quiz intro -->

<quiz>
A WebSocket connection starts life as…

- [x] An ordinary HTTP `GET` with an `Upgrade: websocket` header
- [ ] A raw TCP connection opened straight to the server
- [ ] An HTTP `POST` that the server never finishes answering
- [ ] An HTTP/2 stream kept open with keepalive frames

The handshake is plain HTTP — that's what lets websockets live on the
same port and infrastructure as the rest of the site.
</quiz>

<quiz>
The server agrees to the upgrade with status code [[101]], `Switching Protocols`.
</quiz>

<quiz>
`wss://` differs from `ws://` in that…

- [x] The TLS handshake happens first, then the same upgrade runs inside the tunnel
- [ ] Frames use a different binary format
- [ ] It requires HTTP/2
- [ ] It only supports server → client push

Same protocol, different transport — every frame after the handshake is
identical. Defaults: `ws` on port 80, `wss` on 443.
</quiz>

<quiz>
A page loaded over `https` runs `new WebSocket("ws://…")`. What happens?

- [x] The browser blocks it as mixed content
- [ ] It connects but shows a console warning
- [ ] The browser silently upgrades the URL to `wss://`
- [ ] It falls back to long-polling

That's why every page in `ui/` derives its URL with
`location.origin.replace("http", "ws")` — `http:` → `ws:` and `https:` →
`wss:` come out of the same line.
</quiz>

<quiz>
Compared with a webhook subscriber, a **websocket** subscriber…
*(select all that apply)*

- [x] Needs no public URL — it dials out and holds the line
- [x] Uses the open connection itself as its identity
- [ ] Needs a signature attached to every message
- [ ] Gets automatic retries for events it missed

The socket IS the subscription. The trade: no delivery guarantee — a
socket that's down at broadcast time simply misses the event.
</quiz>

<quiz>
The only place a websocket connection can be authenticated is…

- [x] The upgrade request — headers, query params and cookies arrive once
- [ ] A special `auth` frame sent right after connect
- [ ] A signature field on every message
- [ ] A separate HTTPS request per message

After `101` there are no more requests — just frames on an
already-identified connection. Auth checked *after* `accept()` is too
late: the socket is already open.
</quiz>

<quiz>
A client is disconnected when the server broadcasts an event. That event…

- [x] Is lost — websockets carry no delivery guarantee
- [ ] Is queued and delivered when the client reconnects
- [ ] Is retried with exponential backoff
- [ ] Waits in the hub until the client ACKs it

Catching up needs machinery on top — an HTTP "events since X" endpoint,
or a webhook if the delivery *must* land.
</quiz>

<quiz>
How does the server learn that a client has gone away?

- [x] Only when a read or write on that socket fails
- [ ] The browser always sends a close frame first
- [ ] TCP delivers a disconnect notification immediately
- [ ] The hub polls each client every second

Which is exactly why real servers send protocol-level pings — an idle
NAT or proxy can drop a quiet connection silently, and a ghost socket
looks just like a healthy one until you try to use it.
</quiz>

<quiz>
One slow client is stalling `Hub.broadcast` for everyone. Which fixes
the head-of-line blocking? *(select all that apply)*

- [x] Send to all sockets concurrently with `asyncio.gather`
- [x] Give each connection a bounded `asyncio.Queue` plus its own writer task
- [ ] `await asyncio.sleep(0)` between sends
- [ ] Increase the TCP send window

The queue bound is the subtle part — it's what stops a permanently slow
reader from growing memory forever.
</quiz>

<quiz>
On an `https` page the socket URL must use the [[wss]]:// scheme.

---
`ui/ticker.html` gets this free from
`location.origin.replace("http", "ws")` — `https:` → `wss:`.
</quiz>

<quiz>
Why does the emitter on `/ws/events` receive its own broadcast back?

- [x] It sits on the same feed — the broadcast doubles as the acknowledgement
- [ ] It's a bug in the hub's connection set
- [ ] The server echoes every send for validation
- [ ] The websocket protocol requires it

Seeing your own event return is the cheapest possible confirmation the
server accepted it.
</quiz>

<quiz>
The ticker page needs no recovery logic after a reconnect because…

- [x] The server sends a full `snapshot` on every connect — the feed is disposable
- [ ] The browser replays the last minute of frames
- [ ] The websocket protocol re-sends missed frames automatically
- [ ] The page reconstructs prices client-side

Reconnect + snapshot is the whole recovery story. It works because the
server's state fits in one message — worth remembering when it doesn't.
</quiz>

<!-- mkdocs-quiz results -->
