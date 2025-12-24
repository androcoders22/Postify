"""
User management endpoints.
"""
import io
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from PIL import Image
from config import MONGO_URI
from database import UserRepository
from services import process_logo

router = APIRouter(prefix="/user", tags=["Users"])


@router.post("")
async def create_user(
    logo: UploadFile = File(...),
    phone: str = Form(...),
    mail: str = Form(...),
    website: str = Form(...),
):
    """Create a new user with logo and contact details."""
    if not MONGO_URI:
        raise HTTPException(status_code=500, detail="MONGO_URI not configured")

    try:
        logo_content = await logo.read()
        try:
            logo_content = process_logo(logo_content)
        except Exception as img_err:
            raise HTTPException(
                status_code=400, detail=f"Invalid image file: {str(img_err)}"
            )

        user_id = await UserRepository.create(
            phone=phone,
            mail=mail,
            website=website,
            logo_content=logo_content,
            logo_filename=logo.filename,
        )

        return {
            "status": "success",
            "message": "User created successfully",
            "id": user_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_users():
    """List all users (excluding binary logo for performance)."""
    return await UserRepository.get_all(include_logo=False)


@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get a specific user's details including base64 logo."""
    return await UserRepository.get_by_id(user_id)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    phone: str = Form(None),
    mail: str = Form(None),
    website: str = Form(None),
    logo: UploadFile = File(None),
):
    """Update user details."""
    update_data = {}
    if phone:
        update_data["phone"] = phone
    if mail:
        update_data["mail"] = mail
    if website:
        update_data["website"] = website

    if logo:
        try:
            logo_content = await logo.read()
            update_data["logo"] = process_logo(logo_content)
            update_data["logo_filename"] = logo.filename
        except Exception as img_err:
            raise HTTPException(
                status_code=400, detail=f"Invalid image file: {str(img_err)}"
            )

    return await UserRepository.update(user_id, update_data)


@router.delete("/{user_id}")
async def delete_user(user_id: str):
    """Delete a user."""
    return await UserRepository.delete(user_id)
