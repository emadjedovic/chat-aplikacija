from collections import deque
from threading import Lock
from typing import List
from models.message import Message
from schemas.message import MessageOut
from helper import serialize_message, deserialize_message

MAX_PRIVATE_CHAT_CACHE = 1000

message_cache = {}  # deque
message_cache_lock = Lock()

# (user_id, chat_id) -> last_seen_message_id
last_seen_msg = {}
last_seen_msg_lock = Lock()


def _ensure_chat(chat_id: int):
    exists = chat_id in message_cache
    if not exists:
        message_cache[chat_id] = deque(maxlen=MAX_PRIVATE_CHAT_CACHE)


def add_message_to_cache(msg: Message):
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
        results: List[MessageOut] = []
        for m in message_cache[chat_id]:
            if m["id"] > after_id:
                results.append(deserialize_message(m))
        return results


def set_last_seen(user_id: int, chat_id: int, last_msg_id: int):
    key = (user_id, chat_id)
    with last_seen_msg_lock:
        last_seen_msg[key] = last_msg_id


def get_last_seen(user_id: int, chat_id: int):
    key = (user_id, chat_id)
    with last_seen_msg_lock:
        if key in last_seen_msg:
            return last_seen_msg[key]
        return 0


def get_unread_from_cache(user_id: int, chat_id: int):
    after = get_last_seen(user_id, chat_id)
    return get_new_messages(chat_id, after)


def get_unread_count(user_id: int, chat_id: int):
    unread = get_unread_from_cache(user_id, chat_id)
    return len(unread)
