"""Gom toàn bộ router con của version 1 API."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.predict import router as predict_router
from app.api.v1.farms import router as farms_router
from app.api.v1.disease_info import router as disease_info_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(predict_router)
api_router.include_router(farms_router)
api_router.include_router(disease_info_router)