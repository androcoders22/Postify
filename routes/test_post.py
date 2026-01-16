"""
Test Post Generation Endpoint

Complete end-to-end flow:
1. Fetch today's holiday from DB
2. Generate AI prompt using holiday description
3. Send prompt to Playwright for image generation
4. Apply overlay with subscriber's branding (by subscriber_id)
5. Send to subscriber's WhatsApp number
"""
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from models import GeneratePostResponse
from database import SubscriberRepository
from services import (
    get_holiday_with_description_for_today,
    generate_structured_output,
    generate_image,
    overlay_subscriber_image,
    image_to_base64,
    send_to_whatsapp,
)

router = APIRouter(prefix="/test", tags=["Test"])


@router.post("/generate-post-by-subscriber", response_model=GeneratePostResponse)
async def generate_post_by_subscriber(
    subscriber_id: str = Query(..., description="Subscriber ID from database"),
):
    """
    Generate and send a holiday post for a specific subscriber.

    Flow:
    1. Fetch today's holiday from DB
    2. Get subscriber details by ID
    3. Generate AI prompt
    4. Generate image via Gemini
    5. Apply overlay with subscriber's custom overlay
    6. Send to subscriber's WhatsApp
    """

    print(f"\n[TEST] Starting post generation for subscriber_id: {subscriber_id}")

    # Step 1: Get today's holiday from database
    print("[TEST] Step 1: Fetching today's holiday from database...")
    holiday_data = await get_holiday_with_description_for_today()

    if not holiday_data:
        raise HTTPException(
            status_code=404,
            detail="No holiday found for today in database"
        )

    holiday_prompt = holiday_data.get("prompt", "")
    holiday_description = holiday_data.get("description", "")

    print(f"[TEST] Prompt: {holiday_prompt}")
    print(f"[TEST] Description: {holiday_description}")

    # Step 2: Get subscriber details
    print(f"\n[TEST] Step 2: Fetching subscriber details for ID: {subscriber_id}...")
    try:
        subscriber = await SubscriberRepository.get_by_id(subscriber_id)
        print(f"[TEST]   Subscriber found!")
    except HTTPException as e:
        print(f"[TEST]   HTTPException: {e.detail}")
        raise
    except Exception as e:
        print(f"[TEST]   Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail=f"Error fetching subscriber: {str(e)}"
        )

    subscriber_phone = subscriber.get("phone", "")
    subscriber_name = subscriber.get("name", "")
    subscriber_overlay = subscriber.get("overlay", None)

    print(f"[TEST] Subscriber name: {subscriber_name}")
    print(f"[TEST] Subscriber phone: {subscriber_phone}")
    print(f"[TEST] Subscriber has overlay: {subscriber_overlay is not None}")

    # Step 3: Generate structured output (AI prompt + caption)
    print(f"\n[TEST] Step 3: Generating AI prompt and caption...")
    structured_output = generate_structured_output(holiday_prompt, holiday_description)
    image_prompt = structured_output.get("prompt", "")
    caption = structured_output.get("caption", "")

    if not image_prompt:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate image prompt from AI"
        )

    print(f"[TEST] Generated image prompt (first 100 chars): {image_prompt[:100]}...")
    print(f"[TEST] Generated caption: {caption}")

    # Step 4: Generate image using Gemini
    print(f"\n[TEST] Step 4: Generating image via Gemini...")
    print(f"[TEST] Sending prompt to Gemini...")

    try:
        generated_image = generate_image(image_prompt)
        print(f"[TEST]   Image generated successfully! Size: {generated_image.size}")
    except Exception as e:
        print(f"[TEST]   Gemini image generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Gemini image generation failed: {str(e)}"
        )

    # Step 5: Apply overlay with subscriber's custom overlay
    print(f"\n[TEST] Step 5: Applying subscriber's custom overlay...")

    if not subscriber_overlay:
        print(f"[TEST] ⚠️ No custom overlay found for subscriber, using generated image as-is")
        final_image = generated_image
    else:
        print(f"[TEST] Applying custom overlay (base64 length: {len(subscriber_overlay)} chars)")
        try:
            import base64

            overlay_bytes = base64.b64decode(subscriber_overlay)
            final_image = overlay_subscriber_image(generated_image, overlay_bytes)
            print(f"[TEST] ✅ Overlay applied successfully!")
        except Exception as e:
            print(f"[TEST] ❌ Overlay application failed: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Overlay application failed: {str(e)}"
            )

    # Step 6: Convert to base64 and send to WhatsApp
    print(f"\n[TEST] Step 6: Converting to base64 and sending to WhatsApp...")
    image_base64 = image_to_base64(final_image)
    print(f"[TEST] Image converted to base64 (length: {len(image_base64)} chars)")

    try:
        print(f"[TEST] Sending to WhatsApp number: {subscriber_phone}")
        whatsapp_response = await send_to_whatsapp(image_base64, caption, phone=subscriber_phone)
        print(f"[TEST] WhatsApp API response: {whatsapp_response}")

        return GeneratePostResponse(
            success=True,
            holiday=holiday_prompt,
            caption=caption,
            message=f"Post generated via Gemini and sent to {subscriber_phone} successfully!",
        )
    except Exception as e:
        print(f"[TEST] WhatsApp sending failed: {str(e)}")
        return GeneratePostResponse(
            success=False,
            holiday=holiday_prompt,
            caption=caption,
            message=f"Post generated but failed to send to WhatsApp: {str(e)}",
        )
