from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import random_username.generate as rug
from database import get_db
from schemas.message import MessageOut, MessageIn
from schemas.user import UserOut, UserIn
from crud.global_chat import (
    create_user,
    create_system_join_message,
    mark_user_active,
    list_active_users,
    poll_new_messages,
    send_user_message,
)

router = APIRouter()


@router.get("/generate-username")
def generate_username():
    result = rug.generate_username()[0]
    return {"username": result}


@router.post("/join", response_model=UserOut)
def join(usernameReq: UserIn, db: Session = Depends(get_db)):
    user = create_user(db, usernameReq.username)
    create_system_join_message(db, usernameReq.username)
    return user


@router.get("/users/active")
def get_active_users(current_user_id: int, db: Session = Depends(get_db)):
    mark_user_active(db, current_user_id)
    return list_active_users(db)


@router.get("/messages/unread", response_model=List[MessageOut])
def get_unread_messages(user_id: int, db: Session = Depends(get_db)):
    return poll_new_messages(db, user_id)


@router.post("/messages", response_model=MessageOut)
def post_message(msg: MessageIn, db: Session = Depends(get_db)):
    saved = send_user_message(db, msg)
    if saved is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return saved
