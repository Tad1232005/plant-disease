import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# Sử dụng SQLite In-Memory cho môi trường Test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Giữ kết nối mở trong suốt phiên test
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
    )


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Tạo lại bảng sạch sẽ trước MỖI hàm test, xoá ngay sau khi test xong."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Fixture cung cấp TestClient kết nối tới SQLite In-Memory."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()