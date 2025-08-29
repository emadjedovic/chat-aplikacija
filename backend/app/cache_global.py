from collections import deque

# djeluje kao rolling buffer, automatski se rjesava najstarijih poruka kada dosegne limit
from threading import Lock, Thread
from models.message import Message
from schemas.message import MessageOut, MessageType
from datetime import datetime, timezone, timedelta
import heapq
import time

"""
The Lock is used to prevent concurrent access to shared data, and with is a construct that handles entering and exiting contexts, like acquiring and releasing the lock. "with" ensures that recources are cleaned up properly when the block ends, even if an exception occurs.

If one thread is inside a "with lock: block", other threads trying to acquire the same lock will wait until it's released. This prevents race conditions, e.g., two threads appending to message_cache at the same time, which could corrupt the deque.
"""

MAX_CACHE_SIZE = 1000  # max broj poruka koje cuvamo u memoriji
# za dovoljno velik cache najveci broj poll poziva nece zahtjevati upit nad bazom
message_cache = deque(maxlen=MAX_CACHE_SIZE)
message_cache_lock = Lock()


def serialize_message(msg: Message):
    return {
        "id": msg.id,
        "content": msg.content,
        "username": msg.username,
        "type": msg.type.value,
        "created_at": msg.created_at.isoformat(),
        "user_id": msg.user_id if msg.type == MessageType.USER_MESSAGE else None,
    }


def deserialize(d):
    created_at = d["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    return MessageOut(
        id=d["id"],
        content=d["content"],
        username=d["username"],
        type=d["type"],
        created_at=created_at,
        user_id=d["user_id"] if d["type"] == MessageType.USER_MESSAGE else None,
    )


# svaku novu poruku odmah dodajemo u cache
def add_message_to_cache(msg: Message):
    serialized_msg = serialize_message(msg)
    with message_cache_lock:
        message_cache.append(serialized_msg)


# userima dobavljamo samo poruke koje nisu stigli procitati
# moramo pamtiti dokle je svaki user dosao u citanju poruke
last_seen_msg = (
    {}
)  # mapa user_id -> (index zadnje procitane poruke, zadnji timestamp aktivnosti usera)
last_seen_msg_lock = Lock()
"""
periodnicno cistiti neaktivne usere
min-heap vrijednosti (expiry_time, user_id) radi efikasnosti 
umjesto da idemo O(n) kroz usere, min-heap nam omogucava sve akcije u O(logn) vremenu
skalabilno, nije potrebno pristupati bazi
"""


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
