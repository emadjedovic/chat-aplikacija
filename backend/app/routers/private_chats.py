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
    get_counterpart_user_id,
)
from crud.notifications import (
    create_new_chat_notification,
    create_new_message_notification,
)

router = APIRouter(prefix="/chats", tags=["private chats"])


@router.get("/get-or-create", response_model=ChatOut)
def get_or_create_chat(
    creator_id: int, other_user_id: int, db: Session = Depends(get_db)
):
    chat = crud_get_or_create_chat(db, creator_id, other_user_id)
    recipient_id = get_counterpart_user_id(chat, creator_id)
    create_new_chat_notification(db, recipient_id=recipient_id, chat_id=chat.id)

    return chat


@router.get("/{chat_id}/messages", response_model=List[MessageOut])
def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    return list_messages_for_chat(db, chat_id)


@router.post("/{chat_id}/messages", response_model=MessageOut)
def post_chat_message(chat_id: int, msg_in: MessageIn, db: Session = Depends(get_db)):
    chat = get_chat_by_id(db, chat_id)
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )

    msg = create_message_in_chat(db, chat_id, msg_in)

    recipient_id = get_counterpart_user_id(chat, msg_in.user_id)
    create_new_message_notification(db, recipient_id=recipient_id, chat_id=chat.id)

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
                msg_payload = data.get("data", {})
                chat_id = msg_payload.get("chat_id")

                db = SessionLocal()
                try:
                    chat = get_chat_by_id(db, chat_id)
                    if chat is not None:
                        receiver_id = get_counterpart_user_id(
                            chat, msg_payload.get("sender_id")
                        )
                        await manager.send_personal_message(
                            receiver_id, {"type": "new_message", "data": msg_payload}
                        )
                finally:
                    db.close()

    except WebSocketDisconnect:
        if user_id is not None:
            manager.disconnect(user_id)
