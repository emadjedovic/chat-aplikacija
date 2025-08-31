from models.message import Message
from schemas.message import MessageOut, MessageType
from datetime import datetime
from typing import Dict

def serialize_message(msg: Message):
    result = {
        "id": msg.id,
        "content": msg.content,
        "username": msg.username,
        "type": msg.type.value,
        "created_at": msg.created_at.isoformat(),
        "user_id": None,
    }
    if msg.type == MessageType.USER_MESSAGE:
        result["user_id"] = msg.user_id
    return result

def deserialize_message(data: Dict):
    created_at = data["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    mtype = data["type"]
    user_id = None
    if mtype == MessageType.USER_MESSAGE or mtype == MessageType.USER_MESSAGE.value:
        user_id = data.get("user_id")

    return MessageOut(
        id=data["id"],
        content=data["content"],
        username=data["username"],
        type=mtype,
        created_at=created_at,
        user_id=user_id,
    )
