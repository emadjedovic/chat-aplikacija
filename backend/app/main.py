from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import time

app = FastAPI()

# Store messages + active users
messages = []
users = {}
subscribers = []

# --- MODELS ---
class Message(BaseModel):
    username: str
    text: str

class User(BaseModel):
    username: str


# --- ENDPOINTS ---

# Add user to active list
@app.post("/join")
async def join(user: User):
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
async def send_message(msg: Message):
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
