from collections import deque
from threading import Lock
from typing import Deque, List, Tuple, Optional
from models import Message
from schemas import MessageOut, MessageType
from datetime import datetime

MAX_PRIVATE_CHAT_CACHE = 1000


def serialize_message(msg: Message):
    return {
        "id": msg.id,
        "content": msg.content,
        "username": msg.username,
        "type": msg.type.value,
        "created_at": msg.created_at.isoformat(),
        "user_id": msg.user_id if msg.type == MessageType.USER_MESSAGE else None,
    }


def deserialize(d):
    created_at = d["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    return MessageOut(
        id=d["id"],
        content=d["content"],
        username=d["username"],
        type=d["type"],
        created_at=created_at,
        user_id=d["user_id"] if d["type"] == MessageType.USER_MESSAGE else None,
    )


# chat_id -> deque[serialized_message]
message_cache = {}
message_cache_lock = Lock()

# (user_id, chat_id) -> last_seen_message_id (int) OR 0 if none
last_seen_msg = {}
last_seen_msg_lock = Lock()


# privatna funkcija
def _ensure_chat(chat_id: int):
    if chat_id not in message_cache:
        message_cache[chat_id] = deque(maxlen=MAX_PRIVATE_CHAT_CACHE)


def add_new_message_to_cache(msg: Message):
    if msg.chat_id is None:
        return
    serialized = serialize_message(msg)
    with message_cache_lock:
        _ensure_chat(msg.chat_id)
        message_cache[msg.chat_id].append(serialized)


def get_new_messages(chat_id: int, after_id: int):
    with message_cache_lock:
        if chat_id not in message_cache:
            return []
        # The deque is small; linear scan is fine. Could binary search if needed.
        items = [deserialize(m) for m in message_cache[chat_id] if m["id"] > after_id]
        return items


def set_last_seen(user_id: int, chat_id: int, last_msg_id: int):
    with last_seen_msg_lock:
        last_seen_msg[(user_id, chat_id)] = last_msg_id


def get_last_seen(user_id: int, chat_id: int) -> int:
    with last_seen_msg_lock:
        return last_seen_msg.get((user_id, chat_id), 0)


def get_unread_from_cache(user_id: int, chat_id: int) -> List[MessageOut]:
    after = get_last_seen(user_id, chat_id)
    return get_new_messages(chat_id, after)


def get_unread_count(user_id: int, chat_id: int) -> int:
    return len(get_unread_from_cache(user_id, chat_id))
