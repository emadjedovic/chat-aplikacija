from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from dependencies import get_db
from schemas.notification import NotificationOut
from crud.notifications import (
    mark_notifications_read,
    unread_flags,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])

"""
npr. return {
  "12": true,
  "34": true
}
"""

@router.get("/unread-flags")
def get_unread_flags(
    current_user_id: int,
    db: Session = Depends(get_db),
):
    return unread_flags(db, current_user_id=current_user_id)


@router.post("/mark-read")
def post_mark_read(
    user_id: int,
    chat_id: int,
    db: Session = Depends(get_db),
):
    updated = mark_notifications_read(db, user_id=user_id, chat_id=chat_id)
    return {"updated": updated}
