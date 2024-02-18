import logging
from fastapi import WebSocket
from typing import Dict, List
import asyncio
from websockets.exceptions import WebSocketException
from fastapi.websockets import WebSocketState


logging.basicConfig(filename='_log/connect.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConnectionManagerNotification:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: int):
        """ Accept a new WebSocket connection for the user. """
        await websocket.accept()
        async with self.lock:
            self.active_connections.setdefault(user_id, []).append(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket):
        """ Disconnect a WebSocket connection for the user. """
        async with self.lock:
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    await self._close_websocket(websocket)
                    self.active_connections[user_id].remove(websocket)

    async def _close_websocket(self, websocket: WebSocket):
        """ Close a WebSocket connection. """
        if websocket.client_state in [WebSocketState.CONNECTED, WebSocketState.CONNECTING]:
            try:
                await websocket.close()
            except WebSocketException as e:
                logger.error("Error closing websocket \n" + str(e))
                

    async def send_personal_message(self, message: str, user_id: int):
        """ Send a personal message to a specific user. """
        websockets = self.active_connections.get(user_id, [])
        for websocket in websockets:
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(message)
                except WebSocketException as e:
                    logger.error("Error sending message to websocket\n" + str(e))
                    

    # async def broadcast(self, message: str):
    #     """ Broadcast a message to all connected users. """
    #     async with self.lock:
    #         for user_id, websockets in self.active_connections.items():
    #             for websocket in [ws for ws in websockets if ws.client_state == WebSocketState.CONNECTED]:
    #                 try:
    #                     await websocket.send_text(message)
    #                 except WebSocketException as e:
    #                     logger.error("Error sending message to websocket\n" + str(e))
    #                     pass
