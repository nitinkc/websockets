"""WebSockets — server push over one long-lived connection.

The whole trick:

  client opens ONE connection up front; server pushes on it forever,
  both directions, with almost no per-message cost

A websocket subscriber needs no public URL, no signature, and no retry
log — the open socket IS the subscription. The trade-off: the client must
stay connected, so websockets suit browsers and long-running services,
not the "call me later on a URL I control" job webhooks are for.
"""

import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from backend import store
from backend.ui import page

logger = logging.getLogger(__name__)
router = APIRouter()


class Hub:
    """The set of sockets watching the live event feed.

    Instead of callback URLs we hold open sockets, and "delivering" is
    one send instead of a signed POST with retries.
    """

    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.connections.add(ws)
        logger.info("ws client connected (%d total)", len(self.connections))

    def disconnect(self, ws: WebSocket) -> None:
        self.connections.discard(ws)
        logger.info("ws client disconnected (%d total)", len(self.connections))

    async def broadcast(self, message: dict) -> int:
        """Push one message to every connected client. Returns reach."""
        dead = []
        for ws in self.connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:  # socket died between connect and send
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
        return len(self.connections)


hub = Hub()


def make_event(type_: str, data: dict) -> dict:
    """The event shape that gets broadcast — same idea as a webhook payload."""
    return {
        "id": "evt_" + uuid.uuid4().hex[:12],
        "type": type_,
        "created_at": store.now(),
        "data": data,
    }


@router.websocket("/ws/echo")
async def echo(ws: WebSocket) -> None:
    """The smallest possible websocket: whatever you send comes back."""
    await ws.accept()
    try:
        while True:
            message = await ws.receive()
            if message["type"] == "websocket.disconnect":
                break
            if (text := message.get("text")) is not None:
                await ws.send_text(f"echo: {text}")
            elif (data := message.get("bytes")) is not None:
                await ws.send_bytes(data)
    except WebSocketDisconnect:
        pass


@router.get("/echo", response_class=FileResponse)
async def echo_page() -> FileResponse:
    """Interactive playground for /ws/echo."""
    return page("echo.html")


@router.get("/events", response_class=FileResponse)
async def events_page() -> FileResponse:
    """Interactive playground for /ws/events."""
    return page("events.html")


@router.websocket("/ws/events")
async def events(ws: WebSocket) -> None:
    """The live event feed.

    The socket is the subscription in BOTH directions:

    - every event broadcast lands on this socket — the same JSON body a
      webhook subscriber would get as a POST
    - send {"type": ..., "data": {...}} on it to EMIT an event, which the
      server broadcasts to every connected client (you included — it's
      the cheapest acknowledgement there is)
    """
    await hub.connect(ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
                event = make_event(msg.get("type", "demo.ping"), msg.get("data", {}))
            except json.JSONDecodeError:
                # Plain text becomes a chat-style message.
                event = make_event("message", {"text": raw})
            store.events.append(event)
            reached = await hub.broadcast(event)
            logger.info("event %s broadcast to %d client(s)", event["id"], reached)
    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(ws)
