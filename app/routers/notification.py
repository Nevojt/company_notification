import asyncio
import logging
import websockets
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.connection_manager import ConnectionManagerNotification
from app.database import get_async_session
from app import models, oauth2
from .func_notification import online, check_new_messages, update_user_status
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(filename='_log/notification.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()
manager = ConnectionManagerNotification()

unread_messages = {}

@router.websocket("/notification")
async def web_private_notification(
    websocket: WebSocket,
    token: str,
    session: AsyncSession = Depends(get_async_session)):

    try:
        user = await oauth2.get_current_user(token, session)
        await manager.connect(websocket, user.id)
        logger.info(f"WebSocket connected for user {user.id}")
        
    except Exception as e:
        logger.error(f"Error authenticating user: {e}", exc_info=True)
        await websocket.close(code=1008)
        return

    new_messages_list = []

    try:
        await update_user_status(session, user.id, True)
        while True:
            try:
                # Wait for a message from the client
                # data = await websocket.receive_json()
                # if data.get("action") == "check_messages":
                new_messages_info = await check_new_messages(session, user.id)
                updated = False

                for message in list(new_messages_list):
                    if message not in new_messages_info:
                        new_messages_list.remove(message)
                        updated = True

                for message_info in new_messages_info:
                    if message_info not in new_messages_list:
                        new_messages_list.append(message_info)
                        updated = True

                if updated:
                    await websocket.send_json({"new_message": new_messages_list})
            except asyncio.exceptions.CancelledError:
                break
                        
    except WebSocketDisconnect:
        print("WebSocket disconnect")
        logger.info(f"WebSocket disconnected for user {user.id}")
        manager.disconnect(websocket, user.id)
        await update_user_status(session, user.id, False)
                    

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket: {e}", exc_info=True)
    
            
