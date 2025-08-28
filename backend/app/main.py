from fastapi import FastAPI, Request, HTTPException, status, Depends
from seed import generate_history_data
from database import SessionLocal, engine, Base
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from schemas import *
from models import User, Message, MessageType
import random_username.generate as rug
from dependencies import get_db
from datetime import datetime, timezone, timedelta
from fastapi.middleware.cors import CORSMiddleware
from cache import *
import heapq
import time
from threading import Thread


# pokrece se prije aplikacije (setup) i nakon zatvaranja (ciscenje)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # kreira tabele iz modela
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    generate_history_data(db)
    db.close()

    yield  # app se ovdje pokrece

    # potencijalno zatvoriti konekcije sve
    pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/generate-username")
def generate_username():
    result = rug.generate_username()[0]
    return {"username": result}


@app.post("/join", response_model=UserOut)
def join(usernameReq: UserIn, db: Session = Depends(get_db)):
    db_user = User(username=usernameReq.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    system_msg = Message(
        content=f"{usernameReq.username} joined the chat!",
        type=MessageType.SYSTEM,
        created_at=datetime.now(timezone.utc),
    )
    db.add(system_msg)
    db.commit()
    db.refresh(system_msg)
    add_message_to_cache(system_msg)
    return db_user


@app.get("/active-users")
def get_active_users(current_user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user_id).first()
    if user:
        # update da je user jos uvijek aktivan
        user.last_active = datetime.now(timezone.utc)
        db.commit()

    # samo aktivni useri, odnosno aktivnost do 11s (jer polling radi svakih 5s-10s)
    active_users = (
        db.query(User)
        .filter(User.last_active > (datetime.utcnow() - timedelta(seconds=11)))
        .order_by(User.last_active.desc())
        .all()
    )

    result = []
    for u in active_users:
        # obavijest u slucaju ulaska do 10s
        ten_seconds_before = datetime.utcnow() - timedelta(seconds=10)
        result.append(
            {
                "id": u.id,
                "username": u.username,
                "joined_recently": u.created_at > ten_seconds_before,
            }
        )

    return result


def ensure_datetime(dt):
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    if dt.tzinfo is None:  # make naive -> UTC aware
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# MESSAGES

"""
Dva usera mogu zvati polling na poruke u isto vrijeme, pa tu uskace Lock da
osigura samo jedan request u jednom trenutku koji potencijalno mijenja
zajednicke strukture (message_cache)
"""


@app.get("/messages/new", response_model=list[MessageOut])
def new_messages(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    with lock:
        # ukoliko user nije u ovoj mapi, znaci da nije vidio nista poruka do sad
        # (dobavljanje se vrsi od pocetka - indeksa 0)
        last_seen_msg_id, last_active = last_seen_msg.get(user_id, (0, now))

        if message_cache:
            first_cache_id = message_cache[0]["id"]  # prva poruka u cacheu
            # zadnja poruka u cacheu
            latest_in_cache_id = message_cache[-1]["id"]
        else:
            # prazan cache
            first_cache_id = -1
            latest_in_cache_id = -1

        new_messages = []

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
                    new_messages.append(m)
                elif m["id"] > last_seen_msg_id:
                    new_messages.append(m)
        # ukoliko korisnik ima neprocitanih poruka koje nisu vise u cacheu...
        else:
            db_msgs = (
                db.query(Message)
                .filter(Message.id > last_seen_msg_id)
                .order_by(Message.id.asc())
                .all()
            )
            new_messages = []
            for m in db_msgs:
                serialized = serialize_message(m)
                new_messages.append(serialized)

        if new_messages:
            last_seen_msg_id = max(m["id"] for m in new_messages)

        last_seen_msg[user_id] = (last_seen_msg_id, now)

    result_messages = []
    for m in new_messages:
        msg_des = deserialize(m)
        result_messages.append(msg_des)

    return result_messages


# ovaj metod "ciscenja" nam osigurava da last_seen_msg ostane relativno mala struktura
expiry_heap = []  # (expiry_time, user_id)
expiry_lock = Lock()  # dijeljena struktura, pa nam treba lock


# stavljamo expirty na 5 minuta (300s)
# poziva se na svaku aktivnost usera
def update_expiry_heap(user_id, last_active):
    expiry = last_active + timedelta(seconds=300)
    with expiry_lock:
        heapq.heappush(expiry_heap, (expiry, user_id))


# skeniramo sve usere svakih 15s
# tehnicki user postaje neaktivan ukoliko ne se poll ne pozove unutar 10s,
# ali sigurnosti radi ostavljamo razmak jos 5s
def cleanup_inactive_users():
    while True:
        now = datetime.now(timezone.utc)
        with expiry_lock:
            if expiry_heap:
                expiry, user_id = expiry_heap[0]

        time.sleep(15)

        now = datetime.now(timezone.utc)

        with expiry_lock:
            while expiry_heap:
                next_expiry, user_id = expiry_heap[0]
                if next_expiry > now:
                    break  # korisnik jos uvijek validan
                heapq.heappop(expiry_heap)
                last_seen_msg.pop(user_id, None)


Thread(target=cleanup_inactive_users, daemon=True).start()


@app.post("/send", response_model=MessageOut)
def send_message(msg: MessageIn, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == msg.username).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
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
    now = datetime.now(timezone.utc)
    with lock:
        last_seen_msg_id, last_active = last_seen_msg.get(db_user.id, (0, now))
        last_seen_msg_id = max(last_seen_msg_id, db_msg.id)
        last_seen_msg[db_user.id] = (last_seen_msg_id, now)

    return db_msg


# ZA TESTIRANJE


@app.get("/", tags=["test"])
def read_root(db: Session = Depends(get_db)):
    users_db = db.query(User).all()
    messages_db = db.query(Message).order_by(Message.created_at).all()

    return {"users": users_db, "messages": messages_db}


@app.get("/active-users-test", tags=["test"])
def get_active_users(current_user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user_id).first()
    if user:
        user.last_active = datetime.now(timezone.utc)
        db.commit()
    active_users = db.query(User).order_by(User.last_active.desc()).all()

    result = []
    for u in active_users:
        ten_seconds_before = datetime.utcnow() - timedelta(seconds=20)
        if u.created_at > ten_seconds_before:
            system_msg = Message(
                content=f"{u.username} joined the chat!",
                type=MessageType.SYSTEM,
                created_at=datetime.now(timezone.utc),
            )
            db.add(system_msg)
            db.commit()
            add_message_to_cache(system_msg)

        result.append(
            {
                "id": u.id,
                "username": u.username,
                "joined_recently": u.created_at > ten_seconds_before,
            }
        )

    return result


@app.get("/messages/all", response_model=list[MessageOut], tags=["test"])
def get_messages(db: Session = Depends(get_db)):
    query = db.query(Message).order_by(Message.created_at).all()
    return query
