from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class UserBase(BaseModel):
    username: str


class UserIn(UserBase):
    pass


class UserOut(UserBase):
    id: int
    last_active: datetime

    class Config:
        from_attributes = True
