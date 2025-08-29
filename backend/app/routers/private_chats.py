from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from dependencies import get_db
from database import SessionLocal
from models import Chat, Message, MessageType
from schemas import ChatOut, ChatCreate, MessageOut, MessageIn
from ws_manager import manager
from crud.notifications import create_new_chat_notification, create_new_message_notification

router = APIRouter(prefix="/chats", tags=["private chats"])


@router.get("/get-or-create", response_model=ChatOut)
def get_or_create_chat(creator_id: int, other_user_id: int, db: Session = Depends(get_db)):
    chat = (
        db.query(Chat)
        .filter(
            ((Chat.user1_id == creator_id) & (Chat.user2_id == other_user_id))
            | ((Chat.user1_id == other_user_id) & (Chat.user2_id == creator_id))
        )
        .first()
    )
    if not chat:
        chat = Chat(user1_id=creator_id, user2_id=other_user_id)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        recipient_id = chat.user2_id if chat.user1_id == creator_id else chat.user1_id
        create_new_chat_notification(db, recipient_id=recipient_id, chat_id=chat.id)       
    return chat


@router.get("/{chat_id}/messages", response_model=List[MessageOut])
def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at)
        .all()
    )
    return messages


@router.post("/{chat_id}/messages", response_model=MessageOut)
def post_chat_message(chat_id: int, msg_in: MessageIn, db: Session = Depends(get_db)):
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
    chat = (
        db.query(Chat)
        .filter(
            Chat.id == chat_id
        )
        .first()
    )
    recipient_id = chat.user2_id if chat.user1_id == msg_in.user_id else chat.user1_id
    create_new_message_notification(db, recipient_id=recipient_id, chat_id=chat.id)
    return msg


@router.websocket("/ws")
async def private_chat_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        if data.get("type") != "connect":
            await websocket.close(code=403)
            return
        user_id = data["user_id"]
        await manager.connect(user_id, websocket)

        while True:
            data = await websocket.receive_json()
            if data["type"] == "new_message":
                msg = data["data"]
                chat_id = msg["chat_id"]

                # send to other user in chat
                db = SessionLocal()
                chat = db.query(Chat).filter(Chat.id == chat_id).first()
                if chat:
                    receiver_id = (
                        chat.user2_id
                        if chat.user1_id == msg["sender_id"]
                        else chat.user1_id
                    )
                    await manager.send_personal_message(
                        receiver_id, {"type": "new_message", "data": msg}
                    )
                db.close()
    except WebSocketDisconnect:
        manager.disconnect(user_id)
