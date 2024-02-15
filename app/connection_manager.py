from fastapi import WebSocket
from typing import Dict, List, Optional
import asyncio
from websockets.exceptions import WebSocketException
from fastapi.websockets import WebSocketState

class ConnectionManagerNotification:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        async with self.lock:
            self.active_connections.setdefault(user_id, []).append(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket):
        async with self.lock:
            if user_id in self.active_connections:
                for websocket in self.active_connections[user_id]:
                    await self._close_websocket(websocket)
                del self.active_connections[user_id]

    async def _close_websocket(self, websocket: WebSocket):
        if websocket.client_state in [WebSocketState.CONNECTED, WebSocketState.CONNECTING]:
            try:
                await websocket.close()
            except WebSocketException:
                pass  # Handle specific exceptions if necessary

    async def send_personal_message(self, message: str, user_id: int):
        websockets = self.active_connections.get(user_id, [])
        for websocket in websockets:
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(message)
                except WebSocketException:
                    pass  # Handle specific exceptions if necessary

    async def broadcast(self, message: str):
        async with self.lock:
            for user_id, websockets in self.active_connections.items():
                for websocket in websockets:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        try:
                            await websocket.send_text(message)
                        except WebSocketException:
                            pass  # Handle specific exceptions if necessary
