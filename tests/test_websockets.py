import json
import time

from backend.ws import hub


def test_echo_roundtrips_text(client):
    with client.websocket_connect("/ws/echo") as ws:
        ws.send_text("hello")
        assert ws.receive_text() == "echo: hello"
        ws.send_text("again")
        assert ws.receive_text() == "echo: again"


def test_event_sent_over_socket_is_broadcast(client):
    with client.websocket_connect("/ws/events") as listener:
        with client.websocket_connect("/ws/events") as emitter:
            emitter.send_text(json.dumps({"type": "order.created", "data": {"order_id": 42}}))
            event = json.loads(listener.receive_text())
            assert event["type"] == "order.created"
            assert event["id"].startswith("evt_")
            # The emitter hears its own broadcast too — the broadcast is the ack.
            assert json.loads(emitter.receive_text())["id"] == event["id"]


def test_event_broadcasts_to_all_clients(client):
    with client.websocket_connect("/ws/events") as ws1:
        with client.websocket_connect("/ws/events") as ws2:
            ws1.send_text(json.dumps({"type": "demo.ping", "data": {}}))
            for ws in (ws1, ws2):
                event = json.loads(ws.receive_text())
                assert event["type"] == "demo.ping"
                assert event["id"].startswith("evt_")


def test_plain_text_becomes_a_message_event(client):
    with client.websocket_connect("/ws/events") as ws:
        ws.send_text("hello all")
        event = json.loads(ws.receive_text())
        assert event["type"] == "message"
        assert event["data"]["text"] == "hello all"


def test_client_count_updates_on_disconnect(client):
    with client.websocket_connect("/ws/events"):
        assert len(hub.connections) == 1
    for _ in range(100):
        if not hub.connections:
            break
        time.sleep(0.02)
    assert len(hub.connections) == 0
