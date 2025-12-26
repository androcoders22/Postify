"""
Holiday API Routes - CRUD operations for holidays.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from models.schemas import HolidayCreate, HolidayUpdate, HolidayResponse
from database import HolidayRepository

router = APIRouter(prefix="/holidays", tags=["Holidays"])


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new holiday",
    description="Add a new holiday to the database with date, prompt, and optional description."
)
async def create_holiday(holiday: HolidayCreate):
    """Create a new holiday entry."""
    try:
        holiday_id = await HolidayRepository.create(
            date=holiday.date,
            prompt=holiday.prompt,
            description=holiday.description
        )
        return {
            "status": "success",
            "message": "Holiday created successfully",
            "id": holiday_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create holiday: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[HolidayResponse],
    summary="Get all holidays",
    description="Retrieve all holidays from the database, sorted by date."
)
async def get_all_holidays():
    """Get all holidays."""
    try:
        holidays = await HolidayRepository.get_all()
        return holidays
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch holidays: {str(e)}"
        )


@router.get(
    "/{holiday_id}",
    response_model=HolidayResponse,
    summary="Get holiday by ID",
    description="Retrieve a specific holiday by its MongoDB ObjectId."
)
async def get_holiday_by_id(holiday_id: str):
    """Get a holiday by ID."""
    return await HolidayRepository.get_by_id(holiday_id)


@router.get(
    "/date/{date}",
    response_model=HolidayResponse,
    summary="Get holiday by date",
    description="Retrieve a holiday by its date (DD-MM-YYYY format)."
)
async def get_holiday_by_date(date: str):
    """Get a holiday by date (DD-MM-YYYY format)."""
    holiday = await HolidayRepository.get_by_date(date)
    if not holiday:
        raise HTTPException(
            status_code=404,
            detail=f"No holiday found for date: {date}"
        )
    return holiday


@router.put(
    "/{holiday_id}",
    response_model=dict,
    summary="Update a holiday",
    description="Update an existing holiday's date, prompt, or description."
)
async def update_holiday(holiday_id: str, holiday: HolidayUpdate):
    """Update a holiday by ID."""
    # Build update dict with only provided fields
    update_data = {}
    if holiday.date is not None:
        update_data["date"] = holiday.date
    if holiday.prompt is not None:
        update_data["prompt"] = holiday.prompt
    if holiday.description is not None:
        update_data["description"] = holiday.description

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    return await HolidayRepository.update(holiday_id, update_data)


@router.delete(
    "/{holiday_id}",
    response_model=dict,
    summary="Delete a holiday",
    description="Delete a holiday by its ID."
)
async def delete_holiday(holiday_id: str):
    """Delete a holiday by ID."""
    return await HolidayRepository.delete(holiday_id)


@router.delete(
    "/",
    response_model=dict,
    summary="Delete all holidays",
    description="⚠️ WARNING: This will delete ALL holidays from the database. Use with caution!"
)
async def delete_all_holidays():
    """Delete all holidays (use with caution)."""
    return await HolidayRepository.delete_all()
