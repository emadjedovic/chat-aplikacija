from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from dependencies import get_db
from schemas import NotificationOut
from crud.notifications import (
    list_notifications,
    mark_notifications_read,
    unread_flags,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=List[NotificationOut])
def get_notifications(
    user_id: int,
    db: Session = Depends(get_db),
):
    return list_notifications(db, user_id=user_id)


"""
npr. return {
  "12": true,
  "34": true
}

"""
@router.get("/unread-flags")
def get_unread_flags(
    user_id: int,
    db: Session = Depends(get_db),
):
    return unread_flags(db, user_id=user_id)


@router.post("/mark-read")
def post_mark_read(
    user_id: int = Query(...),
    chat_id: int = Query(...),
    db: Session = Depends(get_db),
):
    updated = mark_notifications_read(db, user_id=user_id, chat_id=chat_id)
    return {"updated": updated}
