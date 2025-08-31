from typing import List
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from dependencies import get_db
from database import SessionLocal
from schemas.chat import ChatOut
from schemas.message import MessageOut, MessageIn
from ws_manager import manager
from crud.private_chats import (
    get_or_create_chat as crud_get_or_create_chat,
    list_messages_for_chat,
    create_message_in_chat,
    get_chat_by_id,
    get_other_user_id,
    persist_message_and_notify
)
from crud.notifications import (
    create_new_chat_notification,
    create_new_message_notification,
)

router = APIRouter(prefix="/chats", tags=["private chats"])


@router.get("/get-or-create", response_model=ChatOut)
async def get_or_create_chat(
    creator_id: int, other_user_id: int, db: Session = Depends(get_db)
):
    chat = crud_get_or_create_chat(db, creator_id, other_user_id)
    recipient_id = get_other_user_id(chat, creator_id)

    # persist notification (so offline user gets it later)
    create_new_chat_notification(db, recipient_id=recipient_id, chat_id=chat.id)

    # push WS notification (instant badge)
    await manager.send_personal_message(
        recipient_id,
        {
            "type": "notification",
            "data": {
                "notification_type": "new_chat",
                "chat_id": chat.id,
                "other_user_id": creator_id,  # who initiated
            },
        },
    )
    return chat



@router.get("/{chat_id}/messages", response_model=List[MessageOut])
def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    return list_messages_for_chat(db, chat_id)


@router.post("/{chat_id}/messages", response_model=MessageOut)
def post_chat_message(chat_id: int, msg_in: MessageIn, db: Session = Depends(get_db)):
    result = persist_message_and_notify(db, chat_id, msg_in)
    if result == (None, None, None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    msg, _, _ = result
    return msg



@router.websocket("/ws")
async def private_chat_ws(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    try:
        data = await websocket.receive_json()
        if data.get("type") != "connect":
            await websocket.close(code=403)
            return

        user_id = data["user_id"]
        await manager.connect(user_id, websocket)

        while True:
            data = await websocket.receive_json()
            if data.get("type") == "new_message":
                payload = data.get("data", {})
                chat_id = payload.get("chat_id")

                db = SessionLocal()
                try:
                    msg_in = MessageIn(
                        content=payload.get("content"),
                        username=payload.get("username"),
                        user_id=payload.get("sender_id"),
                    )
                    result = persist_message_and_notify(db, chat_id, msg_in)
                    if result == (None, None, None):
                        continue
                    msg, recipient_id, chat = result

                    # 1) deliver real message payload (for active view)
                    await manager.send_personal_message(
                        recipient_id,
                        {
                            "type": "new_message",
                            "data": {
                                "id": msg.id,
                                "chat_id": chat_id,
                                "sender_id": msg_in.user_id,
                                "username": msg_in.username,
                                "content": msg_in.content,
                                "created_at": msg.created_at.isoformat(),
                                "type": "user_message",
                            },
                        },
                    )

                    # 2) and a lightweight notification (for sidebar badge)
                    await manager.send_personal_message(
                        recipient_id,
                        {
                            "type": "notification",
                            "data": {
                                "notification_type": "new_message",
                                "chat_id": chat_id,
                                "sender_id": msg_in.user_id,
                            },
                        },
                    )

                finally:
                    db.close()


    except WebSocketDisconnect:
        if user_id is not None:
            manager.disconnect(user_id)
