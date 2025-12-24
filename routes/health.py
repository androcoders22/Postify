"""
Health check endpoint.
"""
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Postify API is running"}
