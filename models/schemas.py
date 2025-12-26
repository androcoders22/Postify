"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GeneratePostResponse(BaseModel):
    """Response model for post generation endpoints."""
    success: bool
    holiday: str
    caption: str
    message: str


class HolidayCreate(BaseModel):
    """Request model for creating a holiday."""
    date: str = Field(..., description="Date in DD-MM-YYYY format", example="25-12-2025")
    prompt: str = Field(..., description="Holiday name/prompt", example="Christmas")
    description: Optional[str] = Field(None, description="Additional description or notes", example="Celebrate the festive season")


class HolidayUpdate(BaseModel):
    """Request model for updating a holiday."""
    date: Optional[str] = Field(None, description="Date in DD-MM-YYYY format")
    prompt: Optional[str] = Field(None, description="Holiday name/prompt")
    description: Optional[str] = Field(None, description="Additional description or notes")


class HolidayResponse(BaseModel):
    """Response model for holiday data."""
    id: str
    date: str
    prompt: str
    description: Optional[str] = None
    created_at: Optional[str] = None
