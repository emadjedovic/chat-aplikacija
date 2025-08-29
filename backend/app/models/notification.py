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

class NotificationType(str, Enum):
    NEW_CHAT = "new_chat"
    NEW_MESSAGE = "new_message"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    type = Column(SQLAlchemyEnum(NotificationType), nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)

    # optional relationships
    recipient = relationship("User")
    chat = relationship("Chat")