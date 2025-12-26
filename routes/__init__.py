"""Postify Routes Package"""
from .health import router as health_router
from .users import router as users_router
from .posts import router as posts_router
from .subscribers import router as subscribers_router
from .holidays import router as holidays_router

__all__ = ["health_router", "users_router", "posts_router", "subscribers_router", "holidays_router"]
