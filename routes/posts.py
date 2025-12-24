"""
Post generation endpoints.
"""
import random
import asyncio
from fastapi import APIRouter, HTTPException, Query
from config import DEFAULT_PHONE_NUMBER
from models import GeneratePostResponse
from database import UserRepository
from services import (
    parse_csv_for_today,
    generate_structured_output,
    generate_image,
    overlay_images,
    image_to_base64,
    send_to_whatsapp,
)

router = APIRouter(tags=["Posts"])


@router.post("/generate-post", response_model=GeneratePostResponse)
async def generate_post(
    holiday: str = Query(None, description="Holiday name (defaults to today's CSV entry)"),
    phone: str = Query(DEFAULT_PHONE_NUMBER, description="Receiver phone number"),
    mail: str = Query("ANDROCODERS21@GMAIL.COM", description="Email for footer"),
    website: str = Query("ANDROCODERS.IN", description="Website for footer"),
):
    """
    Generate and send a custom holiday post.
    Useful for testing specific holidays or branding.
    """
    # Step 1: Resolve Holiday
    if not holiday:
        holiday = parse_csv_for_today()
        if not holiday:
            raise HTTPException(
                status_code=404,
                detail="No holiday found for today and no holiday parameter provided"
            )

    # Step 2: Generate structured output (prompt and caption)
    structured_output = generate_structured_output(holiday)
    image_prompt = structured_output.get("prompt", "")
    caption = structured_output.get("caption", "")

    if not image_prompt:
        raise HTTPException(status_code=500, detail="Failed to generate image prompt")

    # Step 3: Generate and Customize Image
    generated_image = generate_image(image_prompt)

    footer = f"+91 {phone}   |   {mail.upper()}   |   {website.upper()}"
    final_image = overlay_images(generated_image, footer_text=footer)

    # Step 4: Convert to base64
    image_base64 = image_to_base64(final_image)

    # Step 5: Send to WhatsApp
    try:
        await send_to_whatsapp(image_base64, caption, phone=phone)
        return GeneratePostResponse(
            success=True,
            holiday=holiday,
            caption=caption,
            message=f"Post generated and sent to {phone} successfully!",
        )
    except Exception as e:
        return GeneratePostResponse(
            success=False,
            holiday=holiday,
            caption=caption,
            message=f"Post generated but failed to send: {str(e)}",
        )


@router.post("/distribute-holiday-post")
async def distribute_holiday_post():
    """
    Generate a holiday post once and send customized versions to all users
    with randomized staggered delays to avoid rate-limiting/bans.
    """
    # 1. Get Today's Holiday
    holiday = parse_csv_for_today()
    if not holiday:
        return {"status": "error", "message": "No holiday found for today"}

    # 2. Get All Users
    users = await UserRepository.get_all_raw()

    if not users:
        return {"status": "error", "message": "No users found in database"}

    # 3. Generate Base Image (Once)
    structured_output = generate_structured_output(holiday)
    image_prompt = structured_output.get("prompt", "")
    caption = structured_output.get("caption", "")

    if not image_prompt:
        raise HTTPException(status_code=500, detail="Failed to generate image prompt")

    generated_base_image = generate_image(image_prompt)

    # 4. Iterate and Customize with Staggered Delays
    results = []
    total_users = len(users)

    for index, user in enumerate(users):
        try:
            # Custom footer: "Phone | Mail | Website"
            footer = f"{user.get('phone', '')}   |   {user.get('mail', '').upper()}   |   {user.get('website', '').upper()}"

            # Overlay specific logo and footer
            custom_image = overlay_images(
                generated_base_image,
                logo_data=user.get("logo"),
                footer_text=footer
            )

            # Send
            image_b64 = image_to_base64(custom_image)

            # Wait for a random time before sending (except first user)
            if index > 0:
                delay_seconds = random.randint(30, 300)
                print(f"Waiting {delay_seconds} seconds before sending to {user.get('phone')}...")
                await asyncio.sleep(delay_seconds)

            api_res = await send_to_whatsapp(image_b64, caption, phone=user.get("phone"))

            results.append({
                "user_id": str(user["_id"]),
                "phone": user.get("phone"),
                "success": True,
                "api_response": api_res
            })
        except Exception as e:
            results.append({
                "user_id": str(user["_id"]),
                "phone": user.get("phone"),
                "success": False,
                "error": str(e)
            })

    return {
        "status": "completed",
        "holiday": holiday,
        "total_users": total_users,
        "results": results
    }
