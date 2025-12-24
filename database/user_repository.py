"""
User repository for database operations.
"""
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from .connection import get_collection, serialize_doc


class UserRepository:
    """Repository class for user CRUD operations."""

    @staticmethod
    async def create(phone: str, mail: str, website: str, logo_content: bytes, logo_filename: str) -> str:
        """Create a new user and return the inserted ID."""
        user_data = {
            "phone": phone,
            "mail": mail,
            "website": website,
            "logo": logo_content,
            "logo_filename": logo_filename,
            "created_at": datetime.now(),
        }
        result = await get_collection().insert_one(user_data)
        return str(result.inserted_id)

    @staticmethod
    async def get_all(include_logo: bool = False):
        """Get all users. Optionally exclude logo for performance."""
        projection = None if include_logo else {"logo": 0}
        cursor = get_collection().find({}, projection)
        users = []
        async for doc in cursor:
            users.append(serialize_doc(doc))
        return users

    @staticmethod
    async def get_by_id(user_id: str):
        """Get a user by ID."""
        try:
            doc = await get_collection().find_one({"_id": ObjectId(user_id)})
            if not doc:
                raise HTTPException(status_code=404, detail="User not found")
            return serialize_doc(doc)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid User ID or query failed")

    @staticmethod
    async def get_all_raw():
        """Get all users with raw data (for internal use)."""
        cursor = get_collection().find({})
        users = []
        async for doc in cursor:
            users.append(doc)
        return users

    @staticmethod
    async def update(user_id: str, update_data: dict):
        """Update a user by ID."""
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        try:
            result = await get_collection().update_one(
                {"_id": ObjectId(user_id)}, {"$set": update_data}
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="User not found")
            return {"status": "success", "message": "User updated successfully"}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid User ID or update failed")

    @staticmethod
    async def delete(user_id: str):
        """Delete a user by ID."""
        try:
            result = await get_collection().delete_one({"_id": ObjectId(user_id)})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="User not found")
            return {"status": "success", "message": "User deleted successfully"}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid User ID or delete failed")
