from pydantic import BaseModel
from enum import Enum


class NotificationType(str, Enum):
    NEW_CHAT = "new_chat"
    NEW_MESSAGE = "new_message"

class NotificationMarkRead(BaseModel):
    user_id: int

class NotificationOut(BaseModel):
    id: int
    recipient_id: int
    chat_id: int
    type: NotificationType
    is_read: bool

    class Config:
        from_attributes = True
