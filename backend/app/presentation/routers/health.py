"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health check")
def read_health() -> dict[str, str]:
    """Simple health check endpoint for initial environment validation."""
    return {"status": "ok"}
