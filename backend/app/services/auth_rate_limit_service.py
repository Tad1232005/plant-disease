"""PostgreSQL atomic fixed-window limiter shared by all API workers.

Counts successful AND failed attempts; restarting the API does not clear them.
Not a substitute for an ingress/body-size limiter or distributed attack control.
"""
from dataclasses import dataclass
import hashlib
import hmac
from ipaddress import IPv6Address, ip_address, ip_network
import logging
import math

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    retry_after: int
    remaining: int


def subject_key(client_host: str, action: str, secret: str) -> str:
    try:
        address = ip_address(client_host)
        if isinstance(address, IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        if address.version == 6:
            # Do not let one IPv6 allocation bypass the limit by rotating suffixes.
            subject = str(ip_network(f"{address}/64", strict=False))
        else:
            subject = str(address)
    except ValueError:
        subject = "unknown-client"
    return hmac.new(secret.encode(), f"auth-v1|{action}|{subject}".encode(), hashlib.sha256).hexdigest()


def cleanup_expired(db: Session) -> None:
    """Bounded opportunistic cleanup, separate transaction from admission."""
    try:
        db.execute(text("SET LOCAL statement_timeout = '2000ms'"))
        db.execute(text("""
            DELETE FROM auth_rate_limits WHERE bucket_key IN (
                SELECT bucket_key FROM auth_rate_limits
                WHERE expires_at < statement_timestamp() - INTERVAL '1 day'
                ORDER BY expires_at LIMIT 100 FOR UPDATE SKIP LOCKED
            )
        """))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.warning("auth_rate_limit_cleanup_failed")


def consume(db: Session, *, key: str, limit: int, window_seconds: int) -> RateDecision:
    if not (1 <= limit <= 10000 and 1 <= window_seconds <= 3600):
        raise ValueError("Invalid rate policy")
    try:
        db.execute(text("SET LOCAL statement_timeout = '2000ms'"))
        db.execute(text("SET LOCAL lock_timeout = '1000ms'"))
        row = db.execute(text("""
            INSERT INTO auth_rate_limits AS counters (bucket_key, attempts, expires_at)
            VALUES (:key, 1, statement_timestamp() + :window * INTERVAL '1 second')
            ON CONFLICT (bucket_key) DO UPDATE SET
                attempts = CASE WHEN counters.expires_at <= statement_timestamp() THEN 1
                    ELSE LEAST(counters.attempts + 1, :limit + 1) END,
                expires_at = CASE WHEN counters.expires_at <= statement_timestamp()
                    THEN statement_timestamp() + :window * INTERVAL '1 second' ELSE counters.expires_at END
            RETURNING attempts, EXTRACT(EPOCH FROM expires_at - clock_timestamp()) AS retry
        """), {"key": key, "limit": limit, "window": window_seconds}).one()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    attempts = int(row.attempts)
    if attempts == 1:
        cleanup_expired(db)
    return RateDecision(allowed=attempts <= limit, retry_after=max(1, math.ceil(row.retry)),
                        remaining=max(0, limit - attempts))
