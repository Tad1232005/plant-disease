"""Module khởi tạo ứng dụng FastAPI chính."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.release import API_VERSION
from app.schemas.error import ApiError
from app.api.health import router as health_router
from app.api.request_logging import RequestLoggingMiddleware, safe_server_error

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=API_VERSION,
    responses={code: {"model": ApiError} for code in (400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503, 504)},
)
app.add_exception_handler(Exception, safe_server_error)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Retry-After"],
)


@app.middleware("http")
async def private_response_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    if request.url.path.startswith(settings.API_V1_STR + "/auth/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health_router)
app.add_middleware(RequestLoggingMiddleware)


@app.get("/")
def root():
    """Endpoint kiểm tra sức khỏe hệ thống."""
    return {"message": "Plant Disease API is running"}
