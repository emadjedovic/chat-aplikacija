from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from schemas.user import UserOut
from schemas.message import MessageOut

class ChatBase(BaseModel):
    user1_id: int
    user2_id: int


class ChatCreate(ChatBase):
    pass


class ChatOut(ChatBase):
    id: int
    created_at: datetime
    user1: Optional[UserOut] = None
    user2: Optional[UserOut] = None
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True
