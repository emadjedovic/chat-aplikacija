from sqlalchemy.orm import Session
from models.notification import Notification, NotificationType
from models.chat import Chat


def create_new_chat_notification(db: Session, recipient_id: int, chat_id: int):
    notif = Notification(
        recipient_id=recipient_id,
        chat_id=chat_id,
        type=NotificationType.NEW_CHAT,
        is_read=False,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def create_new_message_notification(db: Session, recipient_id: int, chat_id: int):
    notif = Notification(
        recipient_id=recipient_id,
        chat_id=chat_id,
        type=NotificationType.NEW_MESSAGE,
        is_read=False,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def list_notifications(db: Session, user_id: int):
    query = (
        db.query(Notification)
        .filter(Notification.recipient_id == user_id, Notification.is_read == False)
        .all()
    )
    return query


def mark_notifications_read(db: Session, user_id: int, chat_id: int):
    q = db.query(Notification).filter(
        Notification.recipient_id == user_id,
        Notification.chat_id == chat_id,
        Notification.is_read == False,
    )
    updated = q.update({"is_read": True}, synchronize_session=False)
    db.commit()
    return updated


def unread_flags(db: Session, current_user_id: int):
    chats = (
        db.query(Chat)
        .join(Notification, Chat.id == Notification.chat_id)
        .filter(
            Notification.recipient_id == current_user_id,
            Notification.is_read.is_(False),
        )
        .distinct()  # filter duplikate
        .all()
    )

    flags = {}
    for c in chats:
        if c.user1_id == current_user_id:
            other_id = c.user2_id
        else:
            other_id = c.user1_id
        flags[other_id] = True

    return flags
