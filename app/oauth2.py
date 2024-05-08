
from jose import JWTError, jwt
from datetime import datetime, timedelta

from sqlalchemy import select
from . import schemas, database, models
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict):
    """
    Generates a JWT access token.

    Args:
        data (dict): The payload data to be included in the token.

    Returns:
        str: The encoded JWT access token.

    Raises:
        Exception: If there is an error encoding the token.

    This function creates an access token by encoding the provided payload data
    using the JWT library. The token's expiration time is set to the current time
    plus the specified ACCESS_TOKEN_EXPIRE_MINUTES. The encoded token is then
    returned.
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    """
    Verifies the provided access token.

    Args:
        token (str): The access token to be verified.
        credentials_exception (HTTPException): An HTTPException object to be raised if the token cannot be verified.

    Returns:
        schemas.TokenData: The payload data of the verified token, including the user ID.

    Raises:
        HTTPException: If the token cannot be verified.

    This function verifies the provided access token by decoding it using the JWT library. It extracts the user ID from the payload and returns it as a schemas.TokenData object. If the token cannot be verified, it raises an HTTPException with a status code of 401 (Unauthorized) and a custom error message.
    """
    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exception

    return token_data
    
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(database.get_async_session)):
    """
    Retrieves the current user from the database based on the provided access token.

    Args:
        token (str): The access token to be used for authentication.
        db (AsyncSession): The database session to be used for querying the user data.

    Returns:
        models.User: The current user object if the token is valid, otherwise None.

    Raises:
        HTTPException: If the token cannot be verified or the user does not exist in the database.

    This function retrieves the current user from the database based on the provided access token. It first verifies the access token by decoding it and extracting the user ID. Then, it queries the database using the user ID to retrieve the user object. If the token cannot be verified or the user does not exist in the database, it raises an HTTPException with a status code of 401 (Unauthorized) and a custom error message.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate credentials", 
        headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = verify_access_token(token, credentials_exception)
    
    async with db.begin() as session:
        user = await db.execute(select(models.User).filter(models.User.id == token.id))
        user = user.scalar()
    
    return user
