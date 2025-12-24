"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel


class GeneratePostResponse(BaseModel):
    """Response model for post generation endpoints."""
    success: bool
    holiday: str
    caption: str
    message: str
