
import logging
from app import models
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


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
            select(models.PrivateMessage.id, models.PrivateMessage.messages, models.PrivateMessage.fileUrl, models.User.id.label('sender_id'), models.User.user_name)
            .join(models.User, models.PrivateMessage.sender_id == models.User.id)
            .filter(models.PrivateMessage.recipient_id == user_id, models.PrivateMessage.is_read == True)
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


async def online(session: AsyncSession, user_id: int):
    online = await session.execute(select(models.User_Status).filter(models.User_Status.user_id == user_id, models.User_Status.status == True))
    online = online.scalars().all()
    return online

async def update_user_status(session: AsyncSession, user_id: int, is_online: bool):
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

