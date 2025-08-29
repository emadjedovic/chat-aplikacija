from fastapi import FastAPI, Depends
from seed import generate_history_data
from database import SessionLocal, engine, Base
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from models.user import User
from models.message import Message, MessageType
from dependencies import get_db
from datetime import datetime, timezone, timedelta
from fastapi.middleware.cors import CORSMiddleware
from routers import private_chats, notifications, global_chat
from cache_global import add_message_to_cache
from schemas.message import MessageOut


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

app.include_router(private_chats.router)
app.include_router(notifications.router)
app.include_router(global_chat.router)

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
                "username": u.username
            }
        )

    return result


@app.get("/messages/all", response_model=list[MessageOut], tags=["test"])
def get_messages(db: Session = Depends(get_db)):
    query = db.query(Message).order_by(Message.created_at).all()
    return query
