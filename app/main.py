import os
from typing import Any, Dict, List, Set

import redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Realtime Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str) -> None:
        await websocket.accept()
        self.rooms.setdefault(room, set()).add(websocket)
        await self.send_personal_message(websocket, {"type": "system", "text": f"Joined room {room}"})

    async def disconnect(self, websocket: WebSocket, room: str) -> None:
        if room in self.rooms:
            self.rooms[room].discard(websocket)
            if not self.rooms[room]:
                self.rooms.pop(room, None)

    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        await websocket.send_json(message)

    async def broadcast(self, room: str, message: Dict[str, Any]) -> None:
        if redis_client:
            try:
                redis_client.publish(room, message["text"])
            except Exception:
                pass

        for websocket in list(self.rooms.get(room, set())):
            await websocket.send_json(message)

    async def _broadcast(self, room: str, message: Dict[str, Any]) -> None:
        for websocket in list(self.rooms.get(room, set())):
            await websocket.send_json(message)


manager = ConnectionManager()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str) -> None:
    await manager.connect(websocket, room)
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "message":
                await manager.broadcast(room, payload)
            elif payload.get("type") == "ping":
                await manager.send_personal_message(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room)
