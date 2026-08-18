from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password as get_password_hash


def seed_users():
    db = SessionLocal()
    users = [
        {"username": "admin_user", "email": "admin@test.com", "role": "admin"},
        {"username": "manager_user",
         "email": "manager@test.com",
         "role": "manager"},
        {"username": "technician_user",
         "email": "technician@test.com", "role": "technician"},
        {"username": "normal_user", "email": "user@test.com", "role": "user"},
    ]

    for u in users:
        if not db.query(User).filter(User.email == u["email"]).first():
            user = User(
                username=u["username"],
                email=u["email"],
                password_hash=get_password_hash("123456"),
                role=u["role"]
            )
            db.add(user)
    db.commit()
    db.close()


if __name__ == "__main__":
    seed_users()
