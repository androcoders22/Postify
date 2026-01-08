"""
Playwright-backed post generation endpoints.

These endpoints mirror the existing `/generate-post` and distribution endpoints
but use the Playwright automation for image generation instead of the Gemini API.
The prefix `/playwright` keeps them separate and non-breaking.
"""
import random
import asyncio
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from config import DEFAULT_PHONE_NUMBER
from models import GeneratePostResponse
from database import UserRepository
from services import (
    get_holiday_for_today,
    get_holiday_with_description_for_today,
    generate_structured_output,
    overlay_images,
    image_to_base64,
    send_to_whatsapp,
)

# Import the Playwright image generator
from services.playwright_image_service import generate_image_playwright

router = APIRouter(prefix="/playwright", tags=["Playwright Posts"])

# Simple in-memory job tracker for playwright-based distribution
playwright_distribution_jobs = {}


@router.post("/generate-post", response_model=GeneratePostResponse)
async def generate_post_playwright(
    holiday: str = Query(None, description="Holiday name (defaults to today's CSV entry)"),
    phone: str = Query(DEFAULT_PHONE_NUMBER, description="Receiver phone number"),
    mail: str = Query("ANDROCODERS21@GMAIL.COM", description="Email for footer"),
    website: str = Query("ANDROCODERS.IN", description="Website for footer"),
):
    # Resolve holiday
    holiday_description = None
    if not holiday:
        holiday_data = await get_holiday_with_description_for_today()
        if not holiday_data:
            raise HTTPException(
                status_code=404,
                detail="No holiday found for today and no holiday parameter provided",
            )
        holiday = holiday_data.get("prompt")
        holiday_description = holiday_data.get("description")

    structured_output = generate_structured_output(holiday, holiday_description)
    image_prompt = structured_output.get("prompt", "")
    caption = structured_output.get("caption", "")

    if not image_prompt:
        raise HTTPException(status_code=500, detail="Failed to generate image prompt")

    # Generate and Customize Image using Playwright
    generated_image = generate_image_playwright(image_prompt)

    footer = f"+91 {phone}   |   {mail.upper()}   |   {website.upper()}"
    final_image = overlay_images(generated_image, footer_text=footer)

    image_base64 = image_to_base64(final_image)

    try:
        await send_to_whatsapp(image_base64, caption, phone=phone)
        return GeneratePostResponse(
            success=True,
            holiday=holiday,
            caption=caption,
            message=f"Post generated (Playwright) and sent to {phone} successfully!",
        )
    except Exception as e:
        return GeneratePostResponse(
            success=False,
            holiday=holiday,
            caption=caption,
            message=f"Post generated but failed to send: {str(e)}",
        )


@router.post("/distribute-holiday-post")
async def distribute_holiday_post_playwright(background_tasks: BackgroundTasks):
    # 1. Get Today's Holiday with description
    holiday_data = await get_holiday_with_description_for_today()
    if not holiday_data:
        return {"status": "error", "message": "No holiday found for today"}

    holiday = holiday_data.get("prompt")
    holiday_description = holiday_data.get("description")

    # 2. Get All Users
    users = await UserRepository.get_all_raw()

    if not users:
        return {"status": "error", "message": "No users found in database"}

    # 3. Generate Base Image (Once) with Playwright
    structured_output = generate_structured_output(holiday, holiday_description)
    image_prompt = structured_output.get("prompt", "")
    caption = structured_output.get("caption", "")

    if not image_prompt:
        raise HTTPException(status_code=500, detail="Failed to generate image prompt")

    generated_base_image = generate_image_playwright(image_prompt)

    # 4. Create a job ID and start background task
    job_id = str(uuid.uuid4())
    playwright_distribution_jobs[job_id] = {
        "status": "running",
        "holiday": holiday,
        "total_users": len(users),
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "started_at": datetime.now().isoformat(),
        "results": [],
    }

    background_tasks.add_task(
        _process_distribution_playwright,
        job_id,
        users,
        generated_base_image,
        caption,
    )

    return {
        "status": "started",
        "job_id": job_id,
        "holiday": holiday,
        "total_users": len(users),
        "message": f"Playwright distribution started for {len(users)} users. Check status at /playwright/distribution-status/{job_id}",
    }


async def _process_distribution_playwright(job_id: str, users: list, base_image, caption: str):
    job = playwright_distribution_jobs[job_id]

    for index, user in enumerate(users):
        try:
            footer = f"{user.get('phone', '')}   |   {user.get('mail', '').upper()}   |   {user.get('website', '').upper()}"

            custom_image = overlay_images(base_image, logo_data=user.get("logo"), footer_text=footer)

            image_b64 = image_to_base64(custom_image)

            if index > 0:
                delay_seconds = random.randint(30, 300)
                await asyncio.sleep(delay_seconds)

            api_res = await send_to_whatsapp(image_b64, caption, phone=user.get("phone"))

            job["results"].append({
                "user_id": str(user["_id"]),
                "phone": user.get("phone"),
                "success": True,
                "api_response": api_res,
            })
            job["successful"] += 1

        except Exception as e:
            job["results"].append({
                "user_id": str(user["_id"]),
                "phone": user.get("phone"),
                "success": False,
                "error": str(e),
            })
            job["failed"] += 1

        job["processed"] += 1

    job["status"] = "completed"
    job["completed_at"] = datetime.now().isoformat()


@router.get("/distribution-status/{job_id}")
async def get_distribution_status_playwright(job_id: str):
    if job_id not in playwright_distribution_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return playwright_distribution_jobs[job_id]
