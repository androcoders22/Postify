"""
Subscriber repository for database operations.
"""
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from .connection import get_subscribers_collection, serialize_subscriber_doc


class SubscriberRepository:
    """Repository class for subscriber CRUD operations."""

    @staticmethod
    async def create(phone: str, overlay_base64: str, name: str = "") -> str:
        """Create a new subscriber and return the inserted ID."""
        subscriber_data = {
            "name": name,
            "phone": phone,
            "overlay": overlay_base64,  # stored as base64 string
            "created_at": datetime.now(),
        }
        result = await get_subscribers_collection().insert_one(subscriber_data)
        return str(result.inserted_id)

    @staticmethod
    async def get_all():
        """Get all subscribers (excluding overlay for performance)."""
        projection = {"overlay": 0}  # Exclude overlay from list response
        cursor = get_subscribers_collection().find({}, projection)
        subscribers = []
        async for doc in cursor:
            subscribers.append(serialize_subscriber_doc(doc))
        return subscribers

    @staticmethod
    async def get_by_id(subscriber_id: str):
        """Get a subscriber by ID."""
        try:
            doc = await get_subscribers_collection().find_one({"_id": ObjectId(subscriber_id)})
            if not doc:
                raise HTTPException(status_code=404, detail="Subscriber not found")
            return serialize_subscriber_doc(doc)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Subscriber ID or query failed")

    @staticmethod
    async def get_all_raw():
        """Get all subscribers with raw data (for internal use)."""
        cursor = get_subscribers_collection().find({})
        subscribers = []
        async for doc in cursor:
            subscribers.append(doc)
        return subscribers

    @staticmethod
    async def update(subscriber_id: str, update_data: dict):
        """Update a subscriber by ID."""
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        try:
            result = await get_subscribers_collection().update_one(
                {"_id": ObjectId(subscriber_id)}, {"$set": update_data}
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Subscriber not found")
            return {"status": "success", "message": "Subscriber updated successfully"}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Subscriber ID or update failed")

    @staticmethod
    async def delete(subscriber_id: str):
        """Delete a subscriber by ID."""
        try:
            result = await get_subscribers_collection().delete_one({"_id": ObjectId(subscriber_id)})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Subscriber not found")
            return {"status": "success", "message": "Subscriber deleted successfully"}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Subscriber ID or delete failed")
