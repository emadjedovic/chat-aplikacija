from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from enum import Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True)
    last_seen = Column(DateTime, default=datetime.now(timezone.utc))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    messages = relationship("Message", back_populates="user")

class MessageType(str, Enum):
    SYSTEM = "system"
    USER_MESSAGE = "user_message"

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(Text)
    # kada se user izbrise njegove poruke ostaju
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String, nullable=True) # da nam ostane username nakon brisanja usera, null za system poruke
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    type = Column(SQLAlchemyEnum(MessageType), default=MessageType.USER_MESSAGE, nullable=False)

    user = relationship("User", back_populates="messages")
