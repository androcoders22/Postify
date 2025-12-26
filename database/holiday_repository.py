"""
Holiday repository for database operations.
"""
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from typing import Optional, List
from .connection import get_database


def get_holidays_collection():
    """Get the holidays collection."""
    return get_database().get_collection("holidays")


def serialize_holiday_doc(doc):
    """Convert MongoDB holiday document to JSON-serializable dict."""
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    if "created_at" in doc and isinstance(doc["created_at"], datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


class HolidayRepository:
    """Repository class for holiday CRUD operations."""

    @staticmethod
    async def create(date: str, prompt: str, description: Optional[str] = None) -> str:
        """Create a new holiday and return the inserted ID."""
        # Check if holiday with same date already exists
        existing = await get_holidays_collection().find_one({"date": date})
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Holiday with date {date} already exists"
            )

        holiday_data = {
            "date": date,
            "prompt": prompt,
            "description": description,
            "created_at": datetime.now(),
        }
        result = await get_holidays_collection().insert_one(holiday_data)
        return str(result.inserted_id)

    @staticmethod
    async def get_all() -> List[dict]:
        """Get all holidays sorted by date."""
        cursor = get_holidays_collection().find({}).sort("date", 1)
        holidays = []
        async for doc in cursor:
            holidays.append(serialize_holiday_doc(doc))
        return holidays

    @staticmethod
    async def get_by_id(holiday_id: str) -> dict:
        """Get a holiday by ID."""
        try:
            doc = await get_holidays_collection().find_one({"_id": ObjectId(holiday_id)})
            if not doc:
                raise HTTPException(status_code=404, detail="Holiday not found")
            return serialize_holiday_doc(doc)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=400, detail="Invalid Holiday ID or query failed")

    @staticmethod
    async def get_by_date(date: str) -> Optional[dict]:
        """Get a holiday by date (DD-MM-YYYY format)."""
        doc = await get_holidays_collection().find_one({"date": date})
        return serialize_holiday_doc(doc) if doc else None

    @staticmethod
    async def update(holiday_id: str, update_data: dict) -> dict:
        """Update a holiday by ID."""
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        # If updating date, check for duplicates
        if "date" in update_data:
            existing = await get_holidays_collection().find_one({
                "date": update_data["date"],
                "_id": {"$ne": ObjectId(holiday_id)}
            })
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Holiday with date {update_data['date']} already exists"
                )

        try:
            result = await get_holidays_collection().update_one(
                {"_id": ObjectId(holiday_id)}, {"$set": update_data}
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Holiday not found")
            return {"status": "success", "message": "Holiday updated successfully"}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Holiday ID or update failed")

    @staticmethod
    async def delete(holiday_id: str) -> dict:
        """Delete a holiday by ID."""
        try:
            result = await get_holidays_collection().delete_one({"_id": ObjectId(holiday_id)})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Holiday not found")
            return {"status": "success", "message": "Holiday deleted successfully"}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Holiday ID or delete failed")

    @staticmethod
    async def delete_all() -> dict:
        """Delete all holidays (use with caution)."""
        result = await get_holidays_collection().delete_many({})
        return {
            "status": "success",
            "message": f"Deleted {result.deleted_count} holidays"
        }
