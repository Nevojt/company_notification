import asyncio
import logging
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
from app.connection_manager import ConnectionManagerNotification
from app.database import get_async_session
from app import models, oauth2
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession


# Configure logging
logging.basicConfig(filename='_log/notification.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()
manager = ConnectionManagerNotification()

async def check_new_messages(session: AsyncSession, user_id: int):
    """
    Retrieve a list of all the unread private messages sent to the specified user.

    Args:
        session (AsyncSession): The database session.
        user_id (int): The ID of the user.

    Returns:
        List[Dict[str, int]]: Information about unread messages.
    """
    new_messages = await session.execute(
        select(models.PrivateMessage)
        .where(models.PrivateMessage.recipient_id == user_id, models.PrivateMessage.is_read == True)
    )
    return [{"sender_id": message.sender_id, "message_id": message.id} for message in new_messages.scalars().all()]

@router.websocket("/notification")
async def web_private_notification(websocket: WebSocket, token: str, session: AsyncSession = Depends(get_async_session)):
    user = None
    try:
        user = await oauth2.get_current_user(token, session)
        await manager.connect(websocket, user.id)
    except Exception as e:
        logger.error(f"Error authenticating user: {e}", exc_info=True)
        await websocket.close(code=1008)
        return

    try:
        while True:
            if websocket.client_state != WebSocketState.CONNECTED:
                await websocket.send_json({...})

            new_messages_info = await check_new_messages(session, user.id)
            try:
                for message_info in new_messages_info:
                    await websocket.send_json({
                        "type": "new_message",
                        "sender_id": message_info["sender_id"],
                        "message_id": message_info["message_id"]
                    })

                await asyncio.sleep(5)

            except websockets.exceptions.ConnectionClosedOK:
                logger.info(f"WebSocket connection was closed")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket: {e}", exc_info=True)
    finally:
        if user:
            manager.disconnect(user.id, websocket)
        await websocket.close()

