from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class MessageType(str, Enum):
    SYSTEM = "system"
    USER_MESSAGE = "user_message"

class UserBase(BaseModel):
    username: str

class UserIn(UserBase):
    pass

class UserOut(UserBase):
    id: int
    last_online: datetime

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str
    username: Optional[str] = None
    type: MessageType
    user_id: Optional[int]=None

class MessageIn(MessageBase):
    pass

class MessageOut(MessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
