from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from crud.notifications import (
    mark_notifications_read,
    unread_flags,
)
from schemas.notification import NotificationMarkRead

router = APIRouter(prefix="/notifications", tags=["notifications"])

"""
npr. return {
  "12": true,
  "34": true
}
"""


@router.get("/unread")
def get_unread_flags(
    current_user_id: int,
    db: Session = Depends(get_db),
):
    return unread_flags(db, current_user_id=current_user_id)


"""
@router.post("/mark-read")
def post_mark_read(
    user_id: int,
    chat_id: int,
    db: Session = Depends(get_db),
):
    updated = mark_notifications_read(db, user_id=user_id, chat_id=chat_id)
    return {"updated": updated}
"""


# oznacava sve neprocitane notifikacije kao procitane i vraca broj azuriranih redova
@router.patch("/{chat_id}/read")
def mark_notifications_as_read(
    chat_id: int,
    payload: NotificationMarkRead,
    db: Session = Depends(get_db),
):
    updated = mark_notifications_read(db, user_id=payload.user_id, chat_id=chat_id)
    return {"updated": updated}
