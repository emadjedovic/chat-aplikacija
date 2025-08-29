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
    last_active: datetime

    class Config:
        from_attributes = True


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
        from_attributes = True


class ChatBase(BaseModel):
    user1_id: int
    user2_id: int


class ChatCreate(ChatBase):
    pass


class ChatOut(ChatBase):
    id: int
    created_at: datetime
    user1: Optional["UserOut"] = None
    user2: Optional["UserOut"] = None
    messages: List["MessageOut"] = []

    class Config:
        from_attributes = True

class NotificationType(str, Enum):
    NEW_CHAT = "new_chat"
    NEW_MESSAGE = "new_message"

class NotificationOut(BaseModel):
    id: int
    recipient_id: int
    chat_id: int
    type: NotificationType
    is_read: bool

    class Config:
        from_attributes = True

