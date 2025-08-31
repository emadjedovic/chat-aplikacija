from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    Enum as SQLAlchemyEnum,
)
from enum import Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone
from database import Base

class MessageType(str, Enum):
    SYSTEM = "system"
    USER_MESSAGE = "user_message"


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(Text)
    # kada se user izbrise njegove poruke ostaju
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    username = Column(
        String, nullable=True
    )  # da nam ostane username nakon brisanja usera, null za system poruke
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    type = Column(
        SQLAlchemyEnum(MessageType), default=MessageType.USER_MESSAGE, nullable=False
    )

    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=True)
    
    user = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")