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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    generate_history_data(db)
    db.close()

    yield  # 👈 the application runs here

    # Shutdown
    # (put cleanup code here if needed, e.g. closing connections)
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

@app.post("/send")
def send_message(msg: MessageIn, db: Session = Depends(get_db)):
    db_user = db.query(User).filter_by(username=msg.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_msg = Message(content=msg.text, user_id=db_user.id)
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return {"status": "ok", "message_id": db_msg.id}

@app.get("/messages", response_model=list[MessageOut])
def get_messages(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .order_by(Message.timestamp)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return messages