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
    users_list = []
    for u in users_db:
        users_list.append({
            "id": u.id,
            "username": u.username
        })

    messages_db = db.query(Message).order_by(Message.created_at).all()
    messages_list = []
    for m in messages_db:
        user = db.query(User).filter(User.id == m.user_id).first()
        messages_list.append({
            "id": m.id,
            "content": m.content,
            "created_at": m.created_at,
            "username": user.username if user else "Anonimus",
            "type": m.type
        })

    return {
        "users": users_list,
        "messages": messages_list
    }

@app.get("/generate-username")
def generate_username():
    return rug.generate_username()[0]

@app.post("/join")
def join(username: str, db: Session = Depends(get_db)):
    db_user = User(username=username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# poll svakih 5-10 sekundi
@app.get("/active_users")
def get_active_users(current_user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user_id).first()
    if user:
        # update da je user jos uvijek online
        user.last_seen = datetime.now(timezone.utc)
        db.commit()

    # samo aktivni useri, odnosno aktivnost do 20s
    active_users = db.query(User).filter(
        User.last_seen > (datetime.utcnow() - timedelta(seconds=20))
    ).order_by(User.last_seen.desc()).all()

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


        result.append({
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

@app.get("/messages", response_model=list[MessageOut])
def get_messages(db: Session = Depends(get_db)):
    query = db.query(Message).order_by(Message.created_at).all()
    return query

# MESSAGES

from collections import deque
# djeluje kao rolling buffer, automatski se rjesava najstarijih poruka kada dosegne limit
from threading import Lock, Thread
import time

'''
The Lock is used to prevent concurrent access to shared data, and with is a construct that handles entering and exiting contexts, like acquiring and releasing the lock. "with" ensures that recources are cleaned up properly when the block ends, even if an exception occurs.

If one thread is inside a "with lock: block", other threads trying to acquire the same lock will wait until it's released. This prevents race conditions, e.g., two threads appending to message_cache at the same time, which could corrupt the deque.
'''

MAX_CACHE_SIZE = 1000 # max broj poruka koje cuvamo u memoriji
# za dovoljno velik cache najveci broj poll poziva nece zahtjevati upit nad bazom
message_cache = deque(maxlen=MAX_CACHE_SIZE)
lock = Lock()

# svaku novu poruku odmah dodajemo u cache
def add_message_to_cache(msg):
    with lock:
        message_cache.append(msg)

# userima dobavljamo samo poruke koje nisu stigli procitati, moramo pamtiti
# dokle je svaki user dosao u citanju poruke
last_seen_by_users = {} # mapa obicna user id -> (index zadnje procitane poruke, zadnji timestamp aktivnosti usera)
# periodicno cistiti za neaktivne usere

'''
Dva usera mogu zvati polling na poruke u isto vrijeme, pa tu uskace Lock da
osigura samo jedan request u jednom trenutku koji potencijalno mijenja
zajednicke strukture (message_cache)
'''
@app.get("/messages2", response_model=list[MessageOut])
def get_messages2(user_id: int):
    with lock:
        # ukoliko user nije u ovoj mapi, znaci da nije vidio nista poruka do sad
        # (dobavljanje se vrsi od pocetka - indeksa 0)
        start_index = last_seen_by_users.get(user_id, 0)
        # konvertujemo deque u listu prije indeksiranja
        new_messages = list(message_cache)[start_index:]
        # sve poruke procitane (sav cache je vidjen od strane ovog usera)
        last_seen_by_users[user_id] = (
            len(message_cache),
            datetime.now(timezone.utc)
        )

        return new_messages
    

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
    db_user = db.query(User).filter_by(username=msg.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_msg = Message(content=msg.content, user_id=db_user.id, username=db_user.username, type=MessageType.USER_MESSAGE)
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg

