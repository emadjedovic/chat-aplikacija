from faker import Faker
import random
from sqlalchemy.orm import Session
from models import User, Message
from datetime import datetime, timedelta, timezone
from random_username.generate import generate_username

fake = Faker()

def generate_history_data(db: Session, n_users=50, n_messages=500):
    if db.query(User).count() > 0:
        return  # don’t reseed if data exists

    # Create fake users
    users = [User(username=generate_username()[0]) for _ in range(n_users)]
    db.add_all(users)
    db.commit()

    # Refresh to get IDs
    users = db.query(User).all()

    # Create fake messages
    start_time = datetime.now(timezone.utc) - timedelta(days=30)
    messages = []
    for _ in range(n_messages):
        user = random.choice(users)
        msg_time = start_time + timedelta(minutes=random.randint(0, 60*24*30))
        messages.append(
            Message(
                content=fake.sentence(nb_words=random.randint(3,12)),
                timestamp=msg_time,
                user_id=user.id
            )
        )

    db.add_all(messages)
    db.commit()
    print(f"Seeded {n_users} users and {n_messages} messages")
