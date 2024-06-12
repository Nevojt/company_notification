
from http.client import HTTPException
import logging
from app import models
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.schemas import InvitationSchema


# Configure logging
logging.basicConfig(filename='_log/func_notification.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



async def check_new_messages(session: AsyncSession, user_id: int):
    """
    Retrieve a list of all the unread private messages sent to the specified user.

    Args:
        session (AsyncSession): The database session.
        user_id (int): The ID of the user.

    Returns:
        List[Dict[str, int]]: Information about unread messages.
    """
    try:
        # Fetch unread private messages and corresponding sender information
        new_messages = await session.execute(
            select(models.PrivateMessage.id, models.PrivateMessage.message, models.PrivateMessage.fileUrl, models.User.id.label('sender_id'), models.User.user_name)
            .join(models.User, models.PrivateMessage.sender_id == models.User.id)
            .filter(models.PrivateMessage.reciver_id == user_id, models.PrivateMessage.is_read == True)
        )
        messages = new_messages.all()

        # Extract relevant data for each message
        message_data = [
            {
                "sender_id": message.sender_id,
                "sender": message.user_name,
                "message_id": message.id,
                "message": message.messages,
                "fileUrl": message.fileUrl,
            } for message in messages
        ]

        return message_data

    except Exception as e:
        logger.error(f"Error retrieving new messages: {e}", exc_info=True)
        return []

async def get_pending_invitations(session: AsyncSession, user_id: int):
    """
    Retrieve a list of all the pending room invitations sent to the specified user.

    Args:
        session (AsyncSession): The database session.
        user_id (int): The ID of the user.

    Returns:
        List[Dict[str, Any]]: Information about the pending invitations. Each
            invitation is represented as a dictionary with the keys "room",
            "sender", and "invitation_id".
    """
    try:
        result = await session.execute(
        select(models.RoomInvitation)
        .options(joinedload(models.RoomInvitation.room), joinedload(models.RoomInvitation.sender))
        .filter(
            models.RoomInvitation.recipient_id == user_id,
            models.RoomInvitation.status == 'pending'
        )
        )
        invitations = result.scalars().all()

        invitation_data = [
        {
            "room": invitation.room.name_room,
            "sender": invitation.sender.user_name,
            "invitation_id": invitation.id
        } for invitation in invitations
        ]

        return invitation_data
    except Exception as e:
        logger.error(f"Error retrieving pending invitations: {e}", exc_info=True)
        return []

async def get_rooms_state(session: AsyncSession):
    result = await session.execute(select(models.Rooms))
    rooms = result.scalars().all()
    return [(room.id, room.name_room, room.image_room, room.secret_room, room.owner) for room in rooms]

async def online(session: AsyncSession, user_id: int):
    online = await session.execute(select(models.User_Status).filter(models.User_Status.user_id == user_id, models.User_Status.status == True))
    online = online.scalars().all()
    return online

async def update_user_status(session: AsyncSession, user_id: int, is_online: bool):
    """
    Update the status of a user in the database.

    Args:
        session (AsyncSession): The database session.
        user_id (int): The ID of the user.
        is_online (bool): The new status of the user.

    Returns:
        None

    Raises:
        Exception: If an error occurs while updating the user status.
    """
    try:
        await session.execute(
            update(models.User_Status)
            .where(models.User_Status.user_id == user_id)
            .values(status=is_online)
        )
        await session.commit()
        logger.info(f"User status updated for user {user_id}: {is_online}")
    except Exception as e:
        logger.error(f"Error updating user status for user {user_id}: {e}", exc_info=True)

