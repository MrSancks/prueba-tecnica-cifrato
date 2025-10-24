"""FastAPI routers exposed by the presentation layer."""

from fastapi import APIRouter

from .routers import auth, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
