"""FastAPI routers exposed by the presentation layer."""

from fastapi import APIRouter

from .routers import health

api_router = APIRouter()
api_router.include_router(health.router)
