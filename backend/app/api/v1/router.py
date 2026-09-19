"""Gom toàn bộ router con của version 1 API."""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.admin_users import router as admin_users_router
from app.api.v1.endpoints.disease_info import router as disease_info_router
from app.api.v1.endpoints.farm_members import router as farm_members_router
from app.api.v1.endpoints.farms import router as farms_router
from app.api.v1.endpoints.manager_users import router as manager_users_router
from app.api.v1.endpoints.predict import router as predict_router
from app.api.v1.endpoints.scans import router as scans_router
from app.api.v1.endpoints.me import router as me_router
from app.api.v1.endpoints.monitoring import router as monitoring_router
from app.api.v1.endpoints.disease_proposals import router as proposals_router

api_router = APIRouter()
api_router.include_router(me_router)
api_router.include_router(monitoring_router)
api_router.include_router(proposals_router)
api_router.include_router(auth_router)
api_router.include_router(predict_router)
api_router.include_router(farms_router)
api_router.include_router(farm_members_router)
api_router.include_router(disease_info_router)
api_router.include_router(admin_users_router)
api_router.include_router(manager_users_router)
api_router.include_router(scans_router)
