from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class MessageType(str, Enum):
    SYSTEM = "system"
    USER_MESSAGE = "user_message"


class MessageBase(BaseModel):
    content: str
    username: Optional[str] = None
    type: Optional[MessageType] = MessageType.USER_MESSAGE
    user_id: Optional[int] = None


class MessageIn(MessageBase):
    pass


class MessageOut(MessageBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
