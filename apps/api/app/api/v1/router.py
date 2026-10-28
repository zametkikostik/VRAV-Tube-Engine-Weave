"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    billing,
    contact,
    health,
    organizations,
    projects,
    webhooks,
    white_label,
    youtube,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(projects.router)
api_router.include_router(webhooks.router)
api_router.include_router(white_label.router)
api_router.include_router(youtube.router)
api_router.include_router(billing.router)
api_router.include_router(contact.router)
api_router.include_router(admin.router)
