"""Module khởi tạo ứng dụng FastAPI chính."""

from fastapi import FastAPI
from app.api.v1.router import api_router  

app = FastAPI(
    title="Plant Disease Detection API",
    version="1.0.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Endpoint kiểm tra sức khỏe hệ thống."""
    return {"message": "Plant Disease API is running"}