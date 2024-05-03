from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime


    
        
class SocketModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    created_at: datetime
    receiver_id: int
    message: str
    user_name: str
    avatar: str
    is_read: bool

class MessageSchema(BaseModel):
    sender_id: int
    sender: str
    message_id: int
    message: str
    fileUrl: str
        
class InvitationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    room_id: int
    sender_id: int
    status: str
    created_at: datetime
    
class TokenData(BaseModel):
    id: Optional[int] = None
    
    
# class UserCreate(BaseModel):
#     email: EmailStr
#     user_name: str
#     password: str
#     avatar: str
    
        
# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str

        
        



# class UserOut(BaseModel):
#     id: int
#     user_name: str
#     avatar: str
#     created_at: datetime
    
#     class Config:
#         from_attributes = True