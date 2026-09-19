"""Rate-limit costly Auth operations; trust ASGI client, never raw proxy headers."""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.auth_rate_limit_service import consume, subject_key


def require_auth_rate_limit(request: Request, db: Session = Depends(get_db)) -> None:
    if request.method != "POST":
        return
    action = request.url.path.rstrip("/").rsplit("/", 1)[-1]
    limits = {"login": settings.AUTH_LOGIN_RATE_LIMIT, "register": settings.AUTH_REGISTER_RATE_LIMIT,
              "refresh": settings.AUTH_REFRESH_RATE_LIMIT, "change-password": settings.AUTH_PASSWORD_RATE_LIMIT}
    if action not in limits:
        return  # Logout remains usable even after hitting a login quota.
    key = subject_key(request.client.host if request.client else "", action, settings.SECRET_KEY)
    try:
        decision = consume(db, key=key, limit=limits[action], window_seconds=settings.AUTH_RATE_WINDOW_SECONDS)
    except SQLAlchemyError:
        # No fail-open: otherwise outages bypass password-guessing protection.
        raise HTTPException(status_code=503, detail="Auth protection temporarily unavailable",
                            headers={"Retry-After": "5"}) from None
    if not decision.allowed:
        raise HTTPException(status_code=429, detail="Too many auth requests; try again later",
                            headers={"Retry-After": str(decision.retry_after)})
