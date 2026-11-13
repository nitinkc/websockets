import json

from backend import ticker


def test_ticker_sends_full_snapshot_on_connect(client):
    with client.websocket_connect("/ws/ticker") as ws:
        msg = json.loads(ws.receive_text())
        assert msg["type"] == "snapshot"
        assert {q["symbol"] for q in msg["data"]} == set(ticker.prices)
        for q in msg["data"]:
            assert q["change"] == 0
            assert q["dir"] == "flat"


def test_ticker_pushes_ticks_to_all_clients(client):
    with client.websocket_connect("/ws/ticker") as ws1:
        with client.websocket_connect("/ws/ticker") as ws2:
            for ws in (ws1, ws2):
                ws.receive_text()  # snapshot
                tick = json.loads(ws.receive_text())  # next market tick (~1s)
                assert tick["type"] == "tick"
                assert len(tick["data"]) == len(ticker.prices)
                assert {q["dir"] for q in tick["data"]} <= {"up", "down", "flat"}


def test_ticker_client_disconnect_is_dropped(client):
    with client.websocket_connect("/ws/ticker"):
        assert len(ticker.hub.connections) == 1
    assert len(ticker.hub.connections) == 0
