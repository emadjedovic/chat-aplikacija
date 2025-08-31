from datetime import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class UserIn(UserBase):
    pass


class UserOut(UserBase):
    id: int
    last_active: datetime

    class Config:
        orm_mode = True
