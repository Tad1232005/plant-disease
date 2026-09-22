"""Fixtures tích hợp cho API trên PostgreSQL database tách biệt."""

from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import ModelVersion, User
from tests.db_support import drop_database, get_test_database_url, recreate_database


TEST_DATABASE_URL = get_test_database_url()
engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="session", autouse=True)
def postgres_test_database() -> Generator[None, None, None]:
    recreate_database(TEST_DATABASE_URL)
    try:
        yield
    finally:
        engine.dispose()
        drop_database(TEST_DATABASE_URL)


@pytest.fixture
def db_session(postgres_test_database: None) -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_factory(db_session: Session) -> Callable[..., User]:
    def create_user(
        username: str,
        role: str = "user",
        email: str | None = None,
        created_by: int | None = None,
        password: str = "StrongPass123!",
    ) -> User:
        user = User(
            username=username,
            email=email or f"{username}@test.local",
            password_hash=hash_password(password),
            role=role,
            created_by=created_by,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return create_user


@pytest.fixture
def token_headers() -> Callable[[User], dict[str, str]]:
    def build(user: User) -> dict[str, str]:
        token = create_access_token(
            user.id,
            role=user.role,
            token_version=user.token_version,
        )
        return {"Authorization": f"Bearer {token}"}

    return build


@pytest.fixture
def active_model_versions(db_session: Session) -> list[ModelVersion]:
    """Metadata nhẹ cho API test; không load trọng số thật."""
    rows = [
        ModelVersion(
            version_name="efficientnet-b0-test",
            model_type="efficientnet_b0",
            file_path="models/efficientnet.pt",
            classes_path="models/classes.json",
            temperature=1.49,
            sha256="a" * 64,
            is_active=True,
        ),
        ModelVersion(
            version_name="mobilenet-v2-test",
            model_type="mobilenet_v2",
            file_path="models/mobilenet.pt",
            classes_path="models/classes.json",
            temperature=1.0,
            sha256="b" * 64,
            is_active=True,
        ),
        ModelVersion(
            version_name="resnet50-test",
            model_type="resnet50",
            file_path="models/resnet.pt",
            classes_path="models/classes.json",
            temperature=1.49,
            sha256="c" * 64,
            is_active=True,
        ),
    ]
    db_session.add_all(rows)
    db_session.commit()
    return rows


@pytest.fixture
def admin_user(user_factory) -> User:
    return user_factory("admin", role="admin")


@pytest.fixture
def manager_user(user_factory) -> User:
    return user_factory("manager", role="manager")


@pytest.fixture
def other_manager_user(user_factory) -> User:
    return user_factory("manager_2", role="manager")


@pytest.fixture
def normal_user(user_factory) -> User:
    return user_factory("farmer", role="user")


@pytest.fixture
def technician_user(user_factory) -> User:
    return user_factory("technician", role="technician")


@pytest.fixture
def admin_headers(admin_user, token_headers) -> dict[str, str]:
    return token_headers(admin_user)


@pytest.fixture
def manager_headers(manager_user, token_headers) -> dict[str, str]:
    return token_headers(manager_user)


@pytest.fixture
def user_headers(normal_user, token_headers) -> dict[str, str]:
    return token_headers(normal_user)


@pytest.fixture
def technician_headers(technician_user, token_headers) -> dict[str, str]:
    return token_headers(technician_user)
