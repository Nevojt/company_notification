import logging
from fastapi import WebSocket
from typing import Dict, List, Tuple
# from routers.func_notification import update_user_status


logging.basicConfig(filename='_log/connect.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConnectionManagerNotification:
    def __init__(self):
        # List to store active WebSocket connections
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[int, Tuple[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Accepts a new WebSocket connection and stores it in the list of active connections
        and the dictionary of user connections.
        """
        await websocket.accept()
        print("Connect")
        # await update_user_status(session, user_id, is_online=bool)
        self.active_connections.append(websocket)
        self.user_connections[user_id] = (websocket,)

    async def disconnect(self, websocket: WebSocket, user_id):
        """
        Removes a WebSocket connection from the list of active connections and the user
        connections dictionary when a user disconnects.
        """
        print("Disconnecting")
        await websocket.close()
        self.active_connections.remove(websocket)
        self.user_connections.pop(user_id, None)





















# class ConnectionManagerNotification:
#     def __init__(self):
#         self.active_connections: Dict[Tuple[int], WebSocket] = {}

#     async def connect(self, websocket: WebSocket, user_id: int):
#         await websocket.accept()
#         self.active_connections[user_id] = websocket

#     def disconnect(self, user_id: int):
#         self.active_connections.pop(user_id, None)
                

    # async def send_personal_message(self, message: str, user_id: int):
    #     """ Send a personal message to a specific user. """
    #     websockets = self.active_connections.get(user_id, [])
    #     for websocket in websockets:
    #         if websocket.client_state == WebSocketState.CONNECTED:
    #             try:
    #                 await websocket.send_text(message)
    #             except WebSocketException as e:
    #                 logger.error("Error sending message to websocket\n" + str(e))
                    

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
