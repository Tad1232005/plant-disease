"""Operational health only; readiness does NOT certify model availability."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.core.release import SCHEMA_REVISION

router = APIRouter(tags=["Health"])


def database_ready() -> bool:
    # Independent bounded connection, so a saturated request pool cannot hold
    # the health check for the normal 30-second pool timeout.
    engine = create_engine(settings.DATABASE_URL, poolclass=NullPool,
                           connect_args={"connect_timeout": 3, "options": "-c statement_timeout=2000"})
    try:
        with engine.connect() as connection:
            revisions = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
            return revisions == [SCHEMA_REVISION]
    except SQLAlchemyError:
        return False
    finally:
        engine.dispose()


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready", responses={503: {"description": "Database unavailable or schema not current"}})
def ready() -> JSONResponse:
    ok = database_ready()
    return JSONResponse(status_code=200 if ok else 503,
                        content={"status": "ready" if ok else "not_ready", "scope": "database_schema_only"})
