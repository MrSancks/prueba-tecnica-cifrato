from fastapi import APIRouter

from .routers import auth, health, invoices, puc

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(invoices.router)
api_router.include_router(puc.router)
