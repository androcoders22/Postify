"""Postify Routes Package"""
from .health import router as health_router
from .users import router as users_router
from .posts import router as posts_router

__all__ = ["health_router", "users_router", "posts_router"]
