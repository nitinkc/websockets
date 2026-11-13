"""A self-contained websocket playground.

Run:  uv run uvicorn backend.main:app --reload --port 8100
Then: open http://localhost:8100 — the dashboard links to a live page
per socket:

  WS   /ws/echo    minimal echo socket                          (page /echo)
  WS   /ws/events  the live feed — send {type, data} to emit    (page /events)
  WS   /ws/ticker  fake market data — a quote tick each second  (page /ticker)

Plus GET /api/events — JSON snapshot the dashboard polls.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse

from backend import store, ticker
from backend.ui import page
from backend.ws import hub as ws_hub
from backend.ws import router as ws_router

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The "exchange" — a background task pushing ticks for the app's lifetime.
    market = asyncio.create_task(ticker.market_loop())
    yield
    market.cancel()


app = FastAPI(
    title="websockets-101",
    version="0.1.0",
    description="A minimal playground for pushing events over websocket connections.",
    lifespan=lifespan,
)

app.include_router(ws_router)
app.include_router(ticker.router)


# ---------------------------------------------------------------- dashboard


@app.get("/api/events")
async def api_events() -> dict:
    """Snapshot of the broadcast log for the dashboard's polling."""
    return {
        "events": list(reversed(store.events[-30:])),
        "clients": len(ws_hub.connections),
    }


@app.get("/", response_class=FileResponse)
async def dashboard() -> FileResponse:
    return page("index.html")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
