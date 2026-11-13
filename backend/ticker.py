"""A fake market-data feed — server push only, like a real quote stream.

A random walk ticks once a second for a handful of symbols and is
broadcast to every socket on /ws/ticker. Unlike /ws/events, subscribers
never emit anything: connecting IS subscribing, and every message they
get is a quote. The browser page at GET /ticker renders the feed.
"""

import asyncio
import json
import logging
import random

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from backend.ui import page
from backend.ws import Hub

logger = logging.getLogger(__name__)
router = APIRouter()

TICK_SECONDS = 1.0

# Symbol -> last price. This dict is the whole "market".
prices: dict[str, float] = {
    "ACME": 182.50,
    "BRAV": 76.10,
    "CRNT": 24.85,
    "DLTA": 410.20,
    "EMBR": 9.35,
}

hub = Hub()  # sockets watching the ticker


def quote(symbol: str, price: float, prev: float) -> dict:
    change = round(price - prev, 2)
    return {
        "symbol": symbol,
        "price": price,
        "change": change,
        "dir": "up" if change > 0 else "down" if change < 0 else "flat",
    }


def quotes() -> list[dict]:
    """Flat snapshot for a just-connected client (no previous tick yet)."""
    return [quote(s, p, p) for s, p in prices.items()]


async def market_loop() -> None:
    """The exchange: tick every second, push the whole board to everyone."""
    while True:
        await asyncio.sleep(TICK_SECONDS)
        ticks = []
        for symbol, prev in prices.items():
            # Gaussian random walk, floored so a price never crosses zero.
            price = round(max(0.01, prev * (1 + random.gauss(0, 0.004))), 2)
            prices[symbol] = price
            ticks.append(quote(symbol, price, prev))
        reached = await hub.broadcast({"type": "tick", "data": ticks})
        logger.debug("tick broadcast to %d client(s)", reached)


@router.websocket("/ws/ticker")
async def ticker(ws: WebSocket) -> None:
    """The quote stream — pure server push.

    On connect the socket gets a snapshot of every symbol, then a tick
    each second until it closes. The receive loop only exists to notice
    the client going away — nothing it sends matters.
    """
    await hub.connect(ws)
    await ws.send_text(json.dumps({"type": "snapshot", "data": quotes()}))
    try:
        while True:
            message = await ws.receive()
            if message["type"] == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(ws)


@router.get("/ticker", response_class=FileResponse)
async def ticker_page() -> FileResponse:
    return page("ticker.html")
