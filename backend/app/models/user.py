from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, Integer, String

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'manager')", name="ck_users_role"),
    )
