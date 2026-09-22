"""Browser-origin protection for cookie-setting/consuming auth operations.

CORS alone does not stop a browser from sending a request. Non-browser clients
without Origin remain supported; Origin is not a substitute for authentication.
"""
from fastapi import HTTPException, Request

from app.core.config import settings


def require_trusted_auth_origin(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    origins = request.headers.getlist("origin")
    if len(origins) > 1:
        raise HTTPException(status_code=403, detail="Untrusted auth request origin")
    if origins:
        allowed = {*settings.CORS_ORIGINS, settings.PUBLIC_API_ORIGIN}
        if origins[0] not in allowed:
            raise HTTPException(status_code=403, detail="Untrusted auth request origin")
    elif request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(status_code=403, detail="Untrusted auth request origin")
