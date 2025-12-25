"""
Subscriber management endpoints.
"""
import io
import base64
import random
import asyncio
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, BackgroundTasks
from PIL import Image
from config import MONGO_URI
from database import SubscriberRepository
from services import (
    parse_csv_for_today,
    generate_structured_output,
    generate_image,
    overlay_subscriber_image,
    image_to_base64,
    send_to_whatsapp,
)

router = APIRouter(prefix="/subscriber", tags=["Subscribers"])

# In-memory job tracker for subscriber distributions
subscriber_distribution_jobs = {}


@router.post("")
async def create_subscriber(
    overlay: UploadFile = File(...),
    phone: str = Form(...),
):
    """Create a new subscriber with overlay image and phone number."""
    if not MONGO_URI:
        raise HTTPException(status_code=500, detail="MONGO_URI not configured")

    try:
        # Read and validate the overlay image
        overlay_content = await overlay.read()
        try:
            # Validate it's a valid image
            img = Image.open(io.BytesIO(overlay_content))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            # Save back to bytes
            output = io.BytesIO()
            img.save(output, format="PNG")
            overlay_bytes = output.getvalue()
        except Exception as img_err:
            raise HTTPException(
                status_code=400, detail=f"Invalid image file: {str(img_err)}"
            )

        # Convert to base64 for storage
        overlay_base64 = base64.b64encode(overlay_bytes).decode("utf-8")

        subscriber_id = await SubscriberRepository.create(
            phone=phone,
            overlay_base64=overlay_base64,
        )

        return {
            "status": "success",
            "message": "Subscriber created successfully",
            "id": subscriber_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_subscribers():
    """List all subscribers."""
    return await SubscriberRepository.get_all()


@router.get("/{subscriber_id}")
async def get_subscriber(subscriber_id: str):
    """Get a specific subscriber's details."""
    return await SubscriberRepository.get_by_id(subscriber_id)


@router.put("/{subscriber_id}")
async def update_subscriber(
    subscriber_id: str,
    phone: str = Form(None),
    overlay: UploadFile = File(None),
):
    """Update subscriber details."""
    update_data = {}
    if phone:
        update_data["phone"] = phone

    if overlay:
        try:
            overlay_content = await overlay.read()
            img = Image.open(io.BytesIO(overlay_content))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            output = io.BytesIO()
            img.save(output, format="PNG")
            overlay_bytes = output.getvalue()
            update_data["overlay"] = base64.b64encode(overlay_bytes).decode("utf-8")
        except Exception as img_err:
            raise HTTPException(
                status_code=400, detail=f"Invalid image file: {str(img_err)}"
            )

    return await SubscriberRepository.update(subscriber_id, update_data)


@router.delete("/{subscriber_id}")
async def delete_subscriber(subscriber_id: str):
    """Delete a subscriber."""
    return await SubscriberRepository.delete(subscriber_id)


@router.post("/distribute")
async def distribute_to_subscribers(background_tasks: BackgroundTasks):
    """
    Generate a holiday post and send it to all subscribers with their custom overlays.
    
    Returns immediately with a job_id. Use /subscriber/distribution-status/{job_id} to check progress.
    """
    # 1. Get Today's Holiday
    holiday = parse_csv_for_today()
    if not holiday:
        return {"status": "error", "message": "No holiday found for today"}

    # 2. Get All Subscribers
    subscribers = await SubscriberRepository.get_all_raw()

    if not subscribers:
        return {"status": "error", "message": "No subscribers found in database"}

    # 3. Create a job ID and start background task immediately
    job_id = str(uuid.uuid4())
    subscriber_distribution_jobs[job_id] = {
        "status": "running",
        "holiday": holiday,
        "total_subscribers": len(subscribers),
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "started_at": datetime.now().isoformat(),
        "results": []
    }

    # Start background task (image generation happens inside)
    background_tasks.add_task(
        _process_subscriber_distribution,
        job_id,
        subscribers,
        holiday
    )

    return {
        "status": "started",
        "job_id": job_id,
        "holiday": holiday,
        "total_subscribers": len(subscribers),
        "message": f"Distribution started for {len(subscribers)} subscribers. Check status at /subscriber/distribution-status/{job_id}"
    }


async def _process_subscriber_distribution(job_id: str, subscribers: list, holiday: str):
    """Background task to process the subscriber distribution with staggered delays."""
    job = subscriber_distribution_jobs[job_id]
    
    try:
        # Generate Base Image (Once) - now happens in background
        structured_output = generate_structured_output(holiday)
        image_prompt = structured_output.get("prompt", "")
        caption = structured_output.get("caption", "")

        if not image_prompt:
            job["status"] = "failed"
            job["error"] = "Failed to generate image prompt"
            return

        base_image = generate_image(image_prompt)
    except Exception as e:
        job["status"] = "failed"
        job["error"] = f"Image generation failed: {str(e)}"
        return
    
    for index, subscriber in enumerate(subscribers):
        try:
            # Decode overlay from base64
            overlay_base64 = subscriber.get("overlay", "")
            overlay_bytes = base64.b64decode(overlay_base64)
            
            # Composite the overlay on the generated image
            custom_image = overlay_subscriber_image(base_image, overlay_bytes)

            # Convert to base64 for sending
            image_b64 = image_to_base64(custom_image)

            # Wait for a random time before sending (except first subscriber)
            if index > 0:
                delay_seconds = random.randint(30, 300)
                print(f"[Job {job_id}] Waiting {delay_seconds}s before sending to {subscriber.get('phone')}...")
                await asyncio.sleep(delay_seconds)

            api_res = await send_to_whatsapp(image_b64, caption, phone=subscriber.get("phone"))

            job["results"].append({
                "subscriber_id": str(subscriber["_id"]),
                "phone": subscriber.get("phone"),
                "success": True,
                "api_response": api_res
            })
            job["successful"] += 1

        except Exception as e:
            job["results"].append({
                "subscriber_id": str(subscriber["_id"]),
                "phone": subscriber.get("phone"),
                "success": False,
                "error": str(e)
            })
            job["failed"] += 1
        
        job["processed"] += 1
    
    job["status"] = "completed"
    job["completed_at"] = datetime.now().isoformat()
    print(f"[Job {job_id}] Subscriber distribution completed: {job['successful']} successful, {job['failed']} failed")


@router.get("/distribution-status/{job_id}")
async def get_subscriber_distribution_status(job_id: str):
    """
    Check the status of a subscriber distribution job.
    """
    if job_id not in subscriber_distribution_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return subscriber_distribution_jobs[job_id]
