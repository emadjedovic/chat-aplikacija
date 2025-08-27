from fastapi import FastAPI, Request, HTTPException
from seed import generate_history_data
from fastapi import FastAPI, Depends
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

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    users_db = db.query(User).all()
    messages_db = db.query(Message).order_by(Message.created_at).all()

    return {
        "users": users_db,
        "messages": messages_db
    }

@app.get("/generate-username")
def generate_username():
    result = rug.generate_username()[0]
    return {"username": result}

@app.post("/join")
def join(usernameReq: UserIn, db: Session = Depends(get_db)):
    db_user = User(username=usernameReq.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# poll svakih 5-10 sekundi
@app.get("/active-users")
def get_active_users(current_user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user_id).first()
    if user:
        # update da je user jos uvijek online
        user.last_online = datetime.now(timezone.utc)
        db.commit()

    # samo aktivni useri, odnosno aktivnost do 20s
    active_users = db.query(User).filter(
        User.last_online > (datetime.utcnow() - timedelta(seconds=20))
    ).order_by(User.last_online.desc()).all()

    result = []
    for u in active_users:
        # obavijest u slucaju ulaska do 20s
        ten_seconds_before = (datetime.utcnow() - timedelta(seconds=20))
        if u.created_at > ten_seconds_before:
            system_msg = Message(
                content=f"{u.username} joined the chat!",
                type=MessageType.SYSTEM,
                created_at=datetime.now(timezone.utc)
            )
            db.add(system_msg)
            db.commit()
            add_message_to_cache(system_msg)


        result.append({
            "id": u.id,
            "username": u.username,
            "joined_recently": u.created_at > ten_seconds_before
        })

    return result


@app.get("/active-users-test")
def get_active_users(current_user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user_id).first()
    if user:
        user.last_online = datetime.now(timezone.utc)
        db.commit()
    active_users = db.query(User).order_by(User.last_online.desc()).all()

    result = []
    for u in active_users:
        ten_seconds_before = (datetime.utcnow() - timedelta(seconds=20))
        if u.created_at > ten_seconds_before:
            system_msg = Message(
                content=f"{u.username} joined the chat!",
                type=MessageType.SYSTEM,
                created_at=datetime.now(timezone.utc)
            )
            db.add(system_msg)
            db.commit()
            add_message_to_cache(system_msg)


        result.append({
            "id": u.id,
            "username": u.username,
            "joined_recently": u.created_at > ten_seconds_before
        })

    return result

# poll svakih 2-5 sekundi
# fetch samo poruke koje su novije od zadnjeg timestampa
# TO-DO: define last_timestamp
'''
@app.get("/messages", response_model=list[MessageOut])
def get_messages(last_timestamp: datetime = None, db: Session = Depends(get_db)):
    query = db.query(Message)
    if last_timestamp:
        query = query.filter(Message.created_at > last_timestamp)
    query = query.order_by(Message.created_at)
    return query.all()
    '''

@app.get("/messages/all", response_model=list[MessageOut])
def get_messages(db: Session = Depends(get_db)):
    query = db.query(Message).order_by(Message.created_at).all()
    return query

# MESSAGES



'''
Dva usera mogu zvati polling na poruke u isto vrijeme, pa tu uskace Lock da
osigura samo jedan request u jednom trenutku koji potencijalno mijenja
zajednicke strukture (message_cache)
'''
@app.get("/messages/new", response_model=list[MessageOut])
def new_messages(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    with lock:
        # ukoliko user nije u ovoj mapi, znaci da nije vidio nista poruka do sad
        # (dobavljanje se vrsi od pocetka - indeksa 0)
        last_seen_msg_id, _ = last_seen_by_users.get(user_id, (0, now))
        
        if message_cache:
            first_cache_id = message_cache[0]["id"]
            latest_in_cache_id = message_cache[-1]["id"]
        else:
            # nema poruka u cacheu
            first_cache_id = -1
            latest_in_cache_id = -1

        new_messages = []

        if last_seen_msg_id >= first_cache_id and message_cache:
            # vracamo samo neprocitane poruke
            for m in message_cache:
                if m["id"] > last_seen_msg_id:
                    new_messages.append(m)
        # moramo dobaviti i one poruke koje vise nisu u cacheu
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
            last_seen_msg_id = new_messages[-1]["id"]

        last_seen_by_users[user_id] = (last_seen_msg_id, now)

    result_messages = []
    for m in new_messages:
        msg_des = deserialize(m)
        result_messages.append(msg_des)

    return result_messages
    

def cleanup_inactive_users(sleep_seconds=60, threshold=300):
    while True:
        now = datetime.now(timezone.utc)
        inactive_users = []
        for user_id, (last_index, last_active) in last_seen_by_users.items():
            if (now - last_active).total_seconds() > threshold:
                inactive_users.append(user_id)

        for user_id in inactive_users:
            del last_seen_by_users[user_id]
        time.sleep(sleep_seconds)

# thread za ciscenje
Thread(target=cleanup_inactive_users, daemon=True).start()

@app.post("/send")
def send_message(msg: MessageIn, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username==msg.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_msg = Message(content=msg.content, user_id=db_user.id, username=db_user.username, type=MessageType.USER_MESSAGE)
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    add_message_to_cache(db_msg)
    return db_msg

