"""
Holiday Service - MongoDB-based holiday retrieval.
Replaces the old CSV-based implementation.
"""
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from database import HolidayRepository


async def get_holiday_for_today() -> Optional[str]:
    """
    Get today's holiday from MongoDB.
    Returns the holiday prompt if found, None otherwise.
    """
    today = datetime.now().strftime("%d-%m-%Y")

    try:
        holiday = await HolidayRepository.get_by_date(today)
        if holiday:
            return holiday.get("prompt")
        return None
    except HTTPException:
        # If it's a 404, return None (no holiday found)
        return None
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching holiday: {str(e)}"
        )


async def get_holiday_with_description_for_today() -> Optional[dict]:
    """
    Get today's holiday with full details (prompt and description).
    Returns dict with prompt and description if found, None otherwise.
    """
    today = datetime.now().strftime("%d-%m-%Y")

    try:
        holiday = await HolidayRepository.get_by_date(today)
        if holiday:
            return {
                "prompt": holiday.get("prompt"),
                "description": holiday.get("description")
            }
        return None
    except HTTPException:
        return None
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching holiday: {str(e)}"
        )
