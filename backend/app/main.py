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
    # Query all users
    users_db = db.query(User).all()
    users_list = []
    for u in users_db:
        users_list.append({
            "ID": u.id,
            "username": u.username
        })

    # Query all messages
    messages_db = db.query(Message).order_by(Message.created_at).all()
    messages_list = []
    for m in messages_db:
        user = db.query(User).filter(User.id == m.user_id).first()
        messages_list.append({
            "ID": m.id,
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
def get_active_users(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        # update da je user jos uvijek online
        user.last_seen = datetime.now(timezone.utc)
        db.commit()

    active_users = db.query(User).filter(
        User.last_seen > (datetime.utcnow() - timedelta(seconds=10))
    ).order_by(User.last_seen.desc()).all()

    result = []
    for u in active_users:
        if u.created_at > (datetime.utcnow() - timedelta(seconds=10)):
            system_msg = Message(
                content=f"{u.username} joined the chat!",
                type=MessageType.SYSTEM,
                created_at=datetime.now(timezone.utc)
            )
            db.add(system_msg)
            db.commit()


        result.append({
            "username": u.username,
            "joined_recently": u.created_at > (datetime.utcnow() - timedelta(seconds=10))
        })

    return result

# poll svakih 2-5 sekundi
# fetch samo poruke koje su novije od zadnjeg timestampa
# TO-DO: define last_timestamp
@app.get("/messages", response_model=list[MessageOut])
def get_messages(last_timestamp: datetime = None, db: Session = Depends(get_db)):
    query = db.query(Message)
    if last_timestamp:
        query = query.filter(Message.created_at > last_timestamp)
    query = query.order_by(Message.created_at)
    return query.all()



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

