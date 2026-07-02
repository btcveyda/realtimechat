import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_websocket_broadcasts_messages_to_room_members(client):
    with client.websocket_connect("/ws/demo-room") as sender:
        with client.websocket_connect("/ws/demo-room") as receiver:
            welcome_from_sender = sender.receive_json()
            welcome_from_receiver = receiver.receive_json()

            assert welcome_from_sender["type"] == "system"
            assert welcome_from_receiver["type"] == "system"

            sender.send_json({"type": "message", "text": "hello from pytest"})

            sender_message = sender.receive_json()
            receiver_message = receiver.receive_json()

            assert sender_message["type"] == "message"
            assert sender_message["text"] == "hello from pytest"
            assert receiver_message["type"] == "message"
            assert receiver_message["text"] == "hello from pytest"
