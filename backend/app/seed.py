from faker import Faker
import random
from sqlalchemy.orm import Session
from models import User, Message, MessageType
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
                # last seen default trenutno
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

        # 10% sansa da poruka bude tipa SYSTEM (obavijest da se prikljucio novi user)
        if random.random() < 0.1:
            random_type = MessageType.SYSTEM
            username = None  # system poruka nema usera
        else:
            random_type = MessageType.USER_MESSAGE
            username = user.username

        messages.append(
            Message(
                content=fake.sentence(nb_words=random.randint(3,12)),
                created_at=msg_time,
                user_id=user.id,
                username = username,
                type=random_type
            )
        )

    db.add_all(messages)
    db.commit()

    print(f"Ubaceno {n_users} usera i {n_messages} poruka...\n")

    '''
    print("Users:")
    for u in db.query(User).all():
        print(f"ID: {u.id}, Username: {u.username}")

    print("\nMessages:")
    for m in db.query(Message).order_by(Message.created_at).all():
        # username za svaku poruku
        user = db.query(User).filter(User.id == m.user_id).first()
        print(f"[{m.created_at}] {user.username if user else 'Anonimus'}: {m.content}")
        '''
