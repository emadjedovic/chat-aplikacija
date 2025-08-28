
from collections import deque
# djeluje kao rolling buffer, automatski se rjesava najstarijih poruka kada dosegne limit
from threading import Lock, Thread
import time
from models import Message
from schemas import MessageOut, MessageType

'''
The Lock is used to prevent concurrent access to shared data, and with is a construct that handles entering and exiting contexts, like acquiring and releasing the lock. "with" ensures that recources are cleaned up properly when the block ends, even if an exception occurs.

If one thread is inside a "with lock: block", other threads trying to acquire the same lock will wait until it's released. This prevents race conditions, e.g., two threads appending to message_cache at the same time, which could corrupt the deque.
'''

MAX_CACHE_SIZE = 1000 # max broj poruka koje cuvamo u memoriji
# za dovoljno velik cache najveci broj poll poziva nece zahtjevati upit nad bazom
message_cache = deque(maxlen=MAX_CACHE_SIZE)
lock = Lock()

def serialize_message(msg: Message):
    return {
        "id": msg.id,
        "content": msg.content,
        "username": msg.username,
        "type": msg.type.value,
        "created_at": msg.created_at.isoformat(),
        "user_id": msg.user_id if msg.type == MessageType.USER_MESSAGE else None
    }

def deserialize(d):
    return MessageOut(
        id=d["id"],
        content=d["content"],
        username=d["username"],
        type=d["type"],
        created_at=d["created_at"],
        user_id=d["user_id"] if d["type"] == MessageType.USER_MESSAGE else None
    )


# svaku novu poruku odmah dodajemo u cache
def add_message_to_cache(msg: Message):
    serialized_msg = serialize_message(msg)
    with lock:
        message_cache.append(serialized_msg)
        print("\nAdded to cache: ", serialized_msg)


# userima dobavljamo samo poruke koje nisu stigli procitati
# moramo pamtiti dokle je svaki user dosao u citanju poruke
last_seen_msg = {} # mapa user_id -> (index zadnje procitane poruke, zadnji timestamp aktivnosti usera)
'''
periodnicno cistiti neaktivne usere
min-heap vrijednosti (expiry_time, user_id) radi efikasnosti 
umjesto da idemo O(n) kroz usere, min-heap nam omogucava sve akcije u O(logn) vremenu
skalabilno, nije potrebno pristupati bazi
'''