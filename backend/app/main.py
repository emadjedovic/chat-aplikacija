from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import time
from seed import generate_history_data
from fastapi import FastAPI, Depends
from database import SessionLocal, engine, Base
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from schemas import *
from models import User, Message
import random_username.generate as rug
from dependencies import get_db
from datetime import datetime, timezone, timedelta

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

@app.get("/")
def read_root():
    return {"hello": "world"}

@app.get("/generate-username")
def generate_username():
    username = rug.generate_username()
    return {"username": username}

@app.post("/join")
def join(user: UserIn, db: Session = Depends(get_db)):
    db_user = User(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"status": "ok", "username": db_user.username}

# poll svakih 5-10 sekundi
@app.get("/active_users")
def get_active_users(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        # update da je user jos uvijek online
        user.last_seen = datetime.now(timezone.utc)
        db.commit()
    active_users = db.query(User).filter(
        User.last_seen > datetime.now(timezone.utc) - timedelta(seconds=60)
    ).order_by(User.last_seen.desc()).all()
    return [u.username for u in active_users]

# poll svakih 2-5 sekundi
# fetch samo poruke koje su novije od zadnjeg timestampa
@app.get("/messages", response_model=list[MessageOut])
def get_messages(last_timestamp: datetime = None, db: Session = Depends(get_db)):
    query = db.query(Message).order_by(Message.timestamp)
    if last_timestamp:
        query = query.filter(Message.timestamp > last_timestamp)
    return query.all()


@app.post("/send")
def send_message(msg: MessageIn, db: Session = Depends(get_db)):
    db_user = db.query(User).filter_by(username=msg.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_msg = Message(content=msg.content, user_id=db_user.id)
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return {"status": "ok", "message_id": db_msg.id}

