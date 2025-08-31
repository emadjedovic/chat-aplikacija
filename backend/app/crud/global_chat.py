from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from models.message import Message, MessageType
from models.user import User
from schemas.message import MessageIn, MessageOut

from cache.cache_global import (
    message_cache,
    message_cache_lock,
    last_seen_msg,
    add_message_to_cache,
)
from helper import serialize_message, deserialize_message


def get_current_time():
    return datetime.now(timezone.utc)


# konverzija naive -> UTC aware
def ensure_datetime(dt):
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def create_user(db: Session, username: str) -> User:
    user = User(username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_system_join_message(db: Session, username: str):
    system_msg = Message(
        content=f"{username} se pridružio chatu!",
        type=MessageType.SYSTEM,
        created_at=get_current_time(),
    )
    db.add(system_msg)
    db.commit()
    db.refresh(system_msg)
    add_message_to_cache(system_msg)
    return system_msg


def mark_user_active(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_active = get_current_time()
        db.commit()


# samo aktivni useri, odnosno aktivnost do 11s (jer polling radi svakih 5s-10s)
def list_active_users(db: Session):
    active_users = (
        db.query(User)
        .filter(User.last_active > (datetime.utcnow() - timedelta(seconds=11)))
        .order_by(User.last_active.desc())
        .all()
    )

    result = []
    for u in active_users:
        result.append({"id": u.id, "username": u.username})
    return result


# cita iz globalnog cachea
def poll_new_messages(db: Session, user_id: int):
    with message_cache_lock:
        # ukoliko user nije u ovoj mapi, znaci da nije vidio nista poruka do sad
        # (dobavljanje se vrsi od pocetka - indeksa 0)
        last_seen_msg_id, last_active = last_seen_msg.get(
            user_id, (0, get_current_time())
        )

        if message_cache:
            first_cache_id = message_cache[0]["id"]  # prva poruka u cacheu
        else:
            # prazan cache
            first_cache_id = -1

        new_serialized = []

        if message_cache and last_seen_msg_id >= first_cache_id:
            # vracamo samo neprocitane poruke
            # ok za relativno mal cache, npr. do 1000 poruke, efikasnost O(n)
            # MessageType.SYSTEM moguce da imaju manji ID od last_seen_msg_id a da korisnik nije stigao procitati
            for m in message_cache:
                created_at = ensure_datetime(m["created_at"])
                if (
                    m["type"] == MessageType.SYSTEM
                    and created_at > last_seen_msg[user_id][1]
                ):
                    new_serialized.append(m)
                elif m["id"] > last_seen_msg_id:
                    new_serialized.append(m)
        else:
            # ukoliko korisnik ima neprocitanih poruka koje nisu vise u cacheu...
            db_msgs = (
                db.query(Message)
                .filter(Message.id > last_seen_msg_id)
                .order_by(Message.id.asc())
                .all()
            )
            for m in db_msgs:
                serialized = serialize_message(m)
                new_serialized.append(serialized)

        if new_serialized:
            last_seen_msg_id = max(m["id"] for m in new_serialized)

        last_seen_msg[user_id] = (last_seen_msg_id, get_current_time())

    result: list[MessageOut] = []
    for m in new_serialized:
        msg_des = deserialize_message(m)
        result.append(msg_des)

    return result


def send_user_message(db: Session, msg: MessageIn):
    db_user = db.query(User).filter(User.username == msg.username).first()
    if not db_user:
        return None

    db_msg = Message(
        content=msg.content,
        user_id=db_user.id,
        username=db_user.username,
        type=MessageType.USER_MESSAGE,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    add_message_to_cache(db_msg)

    # posiljaocu se ova poruka oznacava kao procitana instantno
    with message_cache_lock:
        last_seen_msg_id, last_active = last_seen_msg.get(
            db_user.id, (0, get_current_time())
        )
        if db_msg.id > last_seen_msg_id:
            last_seen_msg_id = db_msg.id
        last_seen_msg[db_user.id] = (last_seen_msg_id, get_current_time())

    return db_msg
