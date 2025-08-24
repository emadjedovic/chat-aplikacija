from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    username: str

class UserIn(UserBase):
    pass

class UserOut(UserBase):
    id: int
    last_seen: datetime

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str
    username: str

class MessageIn(MessageBase):
    user_id: int

class MessageOut(MessageBase):
    id: int
    timestamp: datetime
    user_id: int
    # optionally include user info
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True
