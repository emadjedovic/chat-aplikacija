from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio
import time
from seed import generate_history_data
from fastapi import FastAPI
from database import SessionLocal, engine, Base
from contextlib import asynccontextmanager
from schemas import *

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


# Store messages + active users
messages = []
users = {}
subscribers = []

@app.get("/generate-username")
def generate_username():
    username = generate_username();
    return {"username": username}


# Add user to active list
@app.post("/join")
async def join(user: UserIn):
    users[user.username] = time.time()
    return {"status": "ok", "username": user.username}

# Get list of active users
@app.get("/users")
async def get_users():
    # remove users inactive >60s
    now = time.time()
    active = [u for u, last_seen in users.items() if now - last_seen < 60]
    return {"users": active}

# Send message
@app.post("/send")
async def send_message(msg: MessageIn):
    entry = f"{msg.username}: {msg.text}"
    messages.append(entry)

    # notify waiting pollers
    for q in subscribers:
        await q.put(entry)
    subscribers.clear()

    return {"status": "ok"}

# Long polling endpoint
@app.get("/poll")
async def poll_messages(request: Request):
    q = asyncio.Queue()
    subscribers.append(q)

    try:
        # wait until new message or client disconnects
        msg = await asyncio.wait_for(q.get(), timeout=30.0)
        return JSONResponse(content={"message": msg})
    except asyncio.TimeoutError:
        # no new messages in 30s → return empty
        return JSONResponse(content={"message": None})
    except Exception:
        return JSONResponse(content={"message": None})
