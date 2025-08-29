# backend/app/crud/private_chats.py
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from models.chat import Chat
from models.message import Message, MessageType
from schemas.message import MessageIn


# ---------- Chat ----------

def get_chat_between(db: Session, user_a_id: int, user_b_id: int) -> Optional[Chat]:
    return (
        db.query(Chat)
        .filter(
            ((Chat.user1_id == user_a_id) & (Chat.user2_id == user_b_id)) |
            ((Chat.user1_id == user_b_id) & (Chat.user2_id == user_a_id))
        )
        .first()
    )


def create_chat(db: Session, user1_id: int, user2_id: int) -> Chat:
    chat = Chat(user1_id=user1_id, user2_id=user2_id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def get_or_create_chat(db: Session, creator_id: int, other_user_id: int) -> Chat:
    chat = get_chat_between(db, creator_id, other_user_id)
    if chat is None:
        chat = create_chat(db, creator_id, other_user_id)
    return chat


def get_chat_by_id(db: Session, chat_id: int) -> Optional[Chat]:
    return db.query(Chat).filter(Chat.id == chat_id).first()


def get_counterpart_user_id(chat: Chat, user_id: int) -> int:
    if chat.user1_id == user_id:
        return chat.user2_id
    return chat.user1_id


# ---------- Messages ----------

def list_messages_for_chat(db: Session, chat_id: int) -> List[Message]:
    return (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )


def create_message_in_chat(db: Session, chat_id: int, msg_in: MessageIn) -> Message:
    msg = Message(
        content=msg_in.content,
        username=msg_in.username,
        user_id=msg_in.user_id,
        chat_id=chat_id,
        type=MessageType.USER_MESSAGE,
        created_at=datetime.now(timezone.utc),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
