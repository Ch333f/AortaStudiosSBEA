from typing import Set
from fastapi import WebSocket
import asyncio


class ConnectionManager:
    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.lock = asyncio.Lock()


    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()

        async with self.lock:
            self.connections.add(ws)


    async def disconnect(self, user_id: str):
        async with self.lock:
            self.connections.discard(user_id)


    async def broadcast(self, payload: dict):
        dead_connections = []

        async with self.lock:
            for ws in self.connections:
                try:
                    await ws.send_json(payload)
                except Exception:
                    dead_connections.append(ws)

            # Clean up dead sockets
            for ws in dead_connections:
                self.connections.discard(ws)
