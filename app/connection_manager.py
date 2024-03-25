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

