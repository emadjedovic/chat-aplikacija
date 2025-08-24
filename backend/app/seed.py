from faker import Faker
import random
from sqlalchemy.orm import Session
from models import User, Message
from datetime import datetime, timedelta, timezone
from random_username.generate import generate_username

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
            )
        )
        
    db.add_all(users)
    db.commit()


    # oduzimamo 30 dana od trenutnog vremena
    start_time = datetime.now(timezone.utc) - timedelta(days=30)
    messages = []
    for _ in range(n_messages):
        user = random.choice(users) # random user

        minutes_in_30_days = 30*24*60
        random_minute_timestamp = random.randint(0, minutes_in_30_days)
        msg_time = start_time + timedelta(minutes=random_minute_timestamp)

        messages.append(
            Message(
                content=fake.sentence(nb_words=random.randint(3,12)),
                timestamp=msg_time,
                user_id=user.id,
                username = user.username
            )
        )

    db.add_all(messages)
    db.commit()

    print(f"Ubaceno {n_users} usera i {n_messages} poruka...\n")

    print("Users:")
    for u in db.query(User).all():
        print(f"ID: {u.id}, Username: {u.username}")

    print("\nMessages:")
    for m in db.query(Message).order_by(Message.timestamp).all():
        # get the username for each message
        user = db.query(User).filter(User.id == m.user_id).first()
        print(f"[{m.timestamp}] {user.username if user else 'Unknown'}: {m.content}")
