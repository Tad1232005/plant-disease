"""Cấu hình Pytest Fixtures, Mock DB In-Memory và Tạo Token theo Role chuẩn Schema."""

# pylint: disable=unexpected-keyword-arg,no-value-for-parameter,redefined-outer-name
# flake8: noqa: E402

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Tạo lại bảng sạch trước mỗi test case và rollback sau khi test xong."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Override dependency get_db để dùng CSDL test."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers(db_session):
    admin = User(
        username="admin_test",
        email="admin@test.com",
        role="admin",
    )
    # gán password_hash sau khi khởi tạo object (constructor model có thể không nhận keyword này)
    admin.password_hash = "hashed_pwd"
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    # create_access_token nhận subject positional (subject: str)
    token = create_access_token(str(admin.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers(db_session):
    manager = User(
        username="manager_test",
        email="manager@test.com",
        role="manager",
    )
    manager.password_hash = "hashed_pwd"
    db_session.add(manager)
    db_session.commit()
    db_session.refresh(manager)
    token = create_access_token(str(manager.id))
    headers = {"Authorization": f"Bearer {token}"}
    return headers, manager.id


@pytest.fixture
def user_headers(db_session):
    """Role 'user' chuẩn theo CHECK constraint của CSDL."""
    user = User(
        username="user_test",
        email="user@test.com",
        role="user",
    )
    user.password_hash = "hashed_pwd"
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}
