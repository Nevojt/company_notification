import asyncio
import logging
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
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
    user = None
    try:
        user = await oauth2.get_current_user(token, session)
        await manager.connect(websocket, user.id)
        await update_user_status(session, user.id, True)
        logger.info(f"WebSocket connected for user {user.id}")
    except Exception as e:
        logger.error(f"Error authenticating user: {e}", exc_info=True)
        await websocket.close(code=1008)
        return

    new_messages_list = []

    try:
        while True:
            if user.id not in manager.online_users:  # Check if user is online
                logger.info(f"User {user.id} is not online. Skipping notification.")
                await asyncio.sleep(5)  # Wait before checking again
                continue

            if not await manager.is_user_connected(user.id):
                logger.info(f"User {user.id} is not connected. Skipping notification.")
                await asyncio.sleep(1)  # Wait for a while before checking again
                continue

            if websocket.client_state != WebSocketState.CONNECTED:
                logger.info(f"WebSocket not connected for user {user.id}, breaking the loop")
                break

            try:
                if await online(session, user.id):
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
                        await websocket.send_json({
                            "new_message": new_messages_list
                        })

                await asyncio.sleep(1)

            except websockets.exceptions.ConnectionClosedOK as e:
                logger.info(f"WebSocket connection was closed for user {user.id}: {e}")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                logger.error(f"WebSocket connection error for user {user.id}: {e}", exc_info=True)
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id}")

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket: {e}", exc_info=True)

    finally:
        if user:
            await update_user_status(session, user.id, False)
            await manager.disconnect(user.id, websocket)
            if websocket.client_state in [WebSocketState.CONNECTED, WebSocketState.DISCONNECTED]:
                await websocket.close()
