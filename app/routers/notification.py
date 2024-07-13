import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.connection_manager import ConnectionManagerNotification
from app.database import get_async_session
from app import oauth2
from .func_notification import get_rooms_state, online, check_new_messages, update_user_status, get_pending_invitations, check_user_password
from .func_notification import user_online_start, user_online_end
from sqlalchemy.ext.asyncio import AsyncSession




# Configure logging
logging.basicConfig(filename='_log/notification.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()
manager = ConnectionManagerNotification()

@router.websocket("/notification")
async def web_private_notification(
    websocket: WebSocket,
    token: str,
    session: AsyncSession = Depends(get_async_session)):

    user = None
    online_session_id = None
    try:
        user = await oauth2.get_current_user(token, session)
        if user.blocked:
            await websocket.close(code=1008)
            return
        
        await manager.connect(websocket, user.id)
        logger.info(f"WebSocket connected for user {user.id}")
        await update_user_status(session, user.id, True)
        
        # online_session_id = await user_online_start(session, user.id)
        
    except Exception as e:
        logger.error(f"Error in WebSocket setup for user: {e}", exc_info=True)
        await websocket.close(code=1008)
        return

    try:
        new_messages_set = set()
        new_invitations_set = set()
        rooms_last_state = await get_rooms_state(session)
        password_changed_state = await check_user_password(session, user.id, False)
        while True:
            await websocket.receive_text()
            
            await asyncio.sleep(1)
            
            password_changed = await check_user_password(session, user.id, True)
            if password_changed_state != password_changed:
                password_changed_state = password_changed
                await websocket.send_json({"logout": True})
                       
            new_messages_info = await check_new_messages(session, user.id)

            # Using set for efficient operations
            current_set = set((msg['message_id'] for msg in new_messages_info))
            if new_messages_set != current_set:
                new_messages_set = current_set
                await websocket.send_json({"new_message": new_messages_info})
                
            
            invitations = await get_pending_invitations(session, user.id)
            invitation_set = set((inv['invitation_id'] for inv in invitations))
            if new_invitations_set!= invitation_set:
                new_invitations_set = invitation_set
                await websocket.send_json({"new_invitations": invitations})
                
                        # Check for changes in the Rooms table
            current_rooms_state = await get_rooms_state(session)
            if rooms_last_state != current_rooms_state:
                rooms_last_state = current_rooms_state
                await websocket.send_json({"update": "room update"})
                
    except asyncio.CancelledError:
    # Handle cancellation (cleanup, logging, etc.)
        pass  
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket for user {user.id}: {e}", exc_info=True)
    finally:
        if user:
            print("WebSocket disconnected")
            await update_user_status(session, user.id, False)
            # if online_session_id:
            #     await user_online_end(session, online_session_id)
                
        await session.close()
        logger.info(f"WebSocket session closed for user {user.id}")

    
            
