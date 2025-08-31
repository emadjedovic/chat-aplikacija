from faker import Faker
import random
from sqlalchemy.orm import Session
from models.user import User
from models.message import Message, MessageType
from datetime import datetime, timedelta, timezone
from random_username.generate import generate_username
from cache.cache_global import add_message_to_cache, message_cache

fake = Faker()


def generate_history_data(db: Session, n_users=50, n_messages=500):

    # ukoliko vec postoje podaci
    if db.query(User).count() > 0:
        return

    users = []
    for _ in range(n_users):
        users.append(
            User(
                # lista of 1 elementa
                username=generate_username()[0]
                # last seen default trenutno
            )
        )

    db.add_all(users)
    db.commit()

    # oduzimamo 30 dana od trenutnog vremena
    start_time = datetime.now(timezone.utc) - timedelta(days=30)

    messages = []
    for i in range(n_messages):
        user = random.choice(users)

        # created_at se povecava za 1s svaku iducu poruku
        msg_time = start_time + timedelta(seconds=i)

        # 10% sansa da bude system poruka
        if random.random() <= 0.1:
            msg_type = MessageType.SYSTEM
            username = None
        else:
            msg_type = MessageType.USER_MESSAGE
            username = user.username

        messages.append(
            Message(
                content=fake.sentence(nb_words=random.randint(3, 12)),
                created_at=msg_time,
                user_id=user.id,
                username=username,
                type=msg_type,
            )
        )

    db.add_all(messages)
    db.commit()

    # da osiguramo id-ove
    for msg in messages:
        db.refresh(msg)

    # osigurati uredjenje po ID
    for msg in sorted(messages, key=lambda m: m.id):
        add_message_to_cache(msg)

    print("Cache velicina: ", len(message_cache))
    print(f"Ubaceno {n_users} usera i {n_messages} poruka...\n")
