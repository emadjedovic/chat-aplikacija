from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    username: str

class UserIn(UserBase):
    pass

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str

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
