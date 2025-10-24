"""Modular FastAPI routers exposed by the presentation layer."""

from . import auth, health

__all__ = ["auth", "health"]
