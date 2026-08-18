"""Module cấu hình engine kết nối CSDL SQLite
    và khởi tạo Session cho ứng dụng."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    """Bật tính năng ràng buộc khóa ngoại (Foreign Keys) cho SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency khởi tạo DB Session cho từng request
        và tự động đóng kết nối khi xử lý xong"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
