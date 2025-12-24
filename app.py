from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
import uvicorn
import csv
import os
import io
import base64
import httpx
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
from bson import ObjectId
import json
import asyncio
import random

# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================
# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# File Paths
CSV_FILE_PATH = "holidays.csv"
OVERLAY_IMAGE_PATH = "overlay.png"
LOGO_IMAGE_PATH = "logo.png"

# API Endpoints
SEND_MEDIA_URL = "https://fast.meteor-fitness.com/send-media?type=base64"
PHONE_NUMBER = "8299396255"

# Gemini Models
GEMINI_TEXT_MODEL = "gemini-flash-latest"
GEMINI_IMAGE_MODEL = "gemini-3-pro-image-preview"

# Image Settings
IMAGE_SIZE = 1024

# Footer Settings
FOOTER_TEXT = "+91 8299396255   |   ANDROCODERS21@GMAIL.COM   |   ANDROCODERS.IN"
FOOTER_ELEVATION = 40
FOOTER_FONT_SIZE = 24
FOOTER_TEXT_COLOR = (255, 255, 255)  # White text

# Prompt Templates - Following Gemini best practices: describe the scene narratively
STRUCTURED_OUTPUT_PROMPT = """You are a creative social media content designer. For the holiday "{holiday}", produce a JSON object with exactly two keys: "prompt" and "caption".

IMPORTANT:
- "prompt" must be a single, flowing, narrative image-generation paragraph suitable for a text-to-image model.
- Do NOT include instructions, bullet points, or meta language inside the "prompt" value.
- Output valid JSON only.

What the image-generation prompt must describe:

Overall scene:
A square 1:1, edge-to-edge premium social media visual with a realistic, studio-quality look. The scene should feel like a carefully styled photographic setup blended with high-end illustration realism, not a flat poster or abstract background.

Composition:
A balanced left–right layout designed for a square crop. Elegant English calligraphic greeting text appears on the LEFT, while a cohesive symbolic vignette appears on the RIGHT. Both sides exist within the same continuous environment and visual plane, with no floating cards, no raised panels, and no framed sections.

LEFT — greeting:
A refined English calligraphy greeting such as “Happy {holiday},” rendered in a sophisticated script. The lettering has a flat metallic or gold-foil appearance with natural light reflections and soft highlights, integrated directly into the scene rather than embossed or extruded. It should feel elegant, premium, and readable at feed scale.

RIGHT — Illustration :
A harmonious grouping of multiple elements (two to four) representing {holiday}, arranged as a small still-life scene rather than a single isolated object. The elements interact naturally subtly, The arrangement feels grounded and intentional, not floating or staged, (Eg: ramadan: crecent moon and lantern,  christmas: tree and snowman...etc)

Background & environment:
Background should be rich with desing and patterns and colors (40%) opacity 

Depth, focus & lighting:
Use deep depth of field so both typography and symbolic elements remain sharp and detailed. Lighting should be soft and diffused with realistic shadows and mild rim-lighting where appropriate. Avoid shallow focus, heavy bokeh, spotlight halos, or blurred backdrops that separate elements from the environment.

Style :
Premium, cinematic, and brand-ready. Photography-like fine material , balanced contrast, and a warm, inviting mood. Avoid logos, watermarks, footer text, UI elements, white margins, flat poster gradients, or card-like compositions.

{{
  "prompt": "<single-paragraph image-generation prompt for an image model (describing the square, left-right scene for {holiday})>",
  "caption": "<short social caption with emojis>"
}}
"""

# ==================== END CONFIGURATION ====================

app = FastAPI(
    title="Postify", description="Automated Holiday Social Media Post Generator"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=GEMINI_API_KEY)

# MongoDB Connection
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.get_database("postify")
collection = db.get_collection("users")


# Helper to convert MongoDB document to JSON-serializable dict
def serialize_doc(doc):
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    if "logo" in doc and isinstance(doc["logo"], bytes):
        doc["logo"] = base64.b64encode(doc["logo"]).decode("utf-8")
    return doc


class GeneratePostResponse(BaseModel):
    success: bool
    holiday: str
    caption: str
    message: str


def parse_csv_for_today() -> str | None:
    """Parse the CSV file and return today's holiday if found."""
    today = datetime.now().strftime("%d-%m-%Y")

    try:
        with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Date"].strip() == today:
                    return row["Prompt"].strip()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500, detail=f"CSV file not found: {CSV_FILE_PATH}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV: {str(e)}")

    return None


def generate_structured_output(holiday: str) -> dict:
    """Generate structured output with prompt and caption using Gemini Flash."""
    prompt = STRUCTURED_OUTPUT_PROMPT.format(holiday=holiday)

    response = client.models.generate_content(
        model=GEMINI_TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    # Parse the JSON response
    import json

    try:
        result = json.loads(response.text)
        print(json.dumps(result, indent=4))
        return result

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, detail="Failed to parse Gemini response as JSON"
        )


def generate_image(prompt: str) -> Image.Image:
    """Generate an image using Gemini Nano Banana Pro."""

    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
                image_size="1K",
            )
        )
    )

    # Extract the generated image from response
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_data = part.inline_data.data
            return Image.open(io.BytesIO(image_data))

    raise HTTPException(status_code=500, detail="No image generated by Gemini")


def overlay_images(
    generated_image: Image.Image,
    logo_data: bytes = None,
    footer_text: str = FOOTER_TEXT,
) -> Image.Image:
    """Overlay the overlay.png and a logo on top of the generated image."""
    # Ensure the generated image is in RGBA mode
    if generated_image.mode != "RGBA":
        generated_image = generated_image.convert("RGBA")

    # Create a copy to work with
    final_image = generated_image.copy()

    # Layer 2: Overlay the overlay.png
    overlay = Image.open(OVERLAY_IMAGE_PATH).convert("RGBA")
    if overlay.size != (IMAGE_SIZE, IMAGE_SIZE):
        overlay = overlay.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
    final_image = Image.alpha_composite(final_image, overlay)

    # Layer 3: Paste the logo on top-left with padding
    if logo_data:
        logo = Image.open(io.BytesIO(logo_data)).convert("RGBA")
    else:
        # Fallback to local default logo if provided
        try:
            logo = Image.open(LOGO_IMAGE_PATH).convert("RGBA")
        except:
            # If no logo at all, skip
            logo = None

    if logo:
        # Resize logo to 120x120
        logo = logo.resize((120, 120), Image.Resampling.LANCZOS)
        # Paste logo at top-left with 20px padding
        final_image.paste(logo, (20, 20), logo)

    # Layer 4: Add footer text
    draw = ImageDraw.Draw(final_image)

    # Use specific Google Sans font only
    font_path = "GoogleSans_17pt-SemiBold.ttf"

    try:
        font = ImageFont.truetype(font_path, FOOTER_FONT_SIZE)
    except (IOError, OSError):
        print(
            f"Warning: Could not load {font_path}, falling back to default (size will be small)"
        )
        font = ImageFont.load_default()

    # Calculate text position (centered horizontally)
    text_bbox = draw.textbbox((0, 0), footer_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (IMAGE_SIZE - text_width) // 2
    y = IMAGE_SIZE - FOOTER_ELEVATION - text_height

    # Draw the footer text
    draw.text((x, y), footer_text, font=font, fill=FOOTER_TEXT_COLOR)

    return final_image


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    # Convert to RGB if needed (for JPEG compatibility)
    if image.mode == "RGBA":
        # Create a white background
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


async def send_to_whatsapp(image_base64: str, caption: str, phone: str = PHONE_NUMBER) -> dict:
    """Send the final image to WhatsApp via API."""
    payload = {"phone": phone, "message": image_base64, "caption": caption}

    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(SEND_MEDIA_URL, json=payload, timeout=60.0)
        return response.json()


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Postify API is running"}


@app.post("/generate-post", response_model=GeneratePostResponse)
async def generate_post(
    holiday: str = Query(None, description="Holiday name (defaults to today's CSV entry)"),
    phone: str = Query(PHONE_NUMBER, description="Receiver phone number"),
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
            raise HTTPException(status_code=404, detail="No holiday found for today and no holiday parameter provided")

    # Step 2: Generate structured output (prompt and caption)
    structured_output = generate_structured_output(holiday)
    image_prompt = structured_output.get("prompt", "")
    caption = structured_output.get("caption", "")

    if not image_prompt:
        raise HTTPException(status_code=500, detail="Failed to generate image prompt")

    # Step 3: Generate and Customize Image
    generated_image = generate_image(image_prompt)
    
    footer = f"{phone}   |   {mail.upper()}   |   {website.upper()}"
    final_image = overlay_images(generated_image, footer_text=footer)

    # Step 4: Convert to base64
    image_base64 = image_to_base64(final_image)

    # Step 5: Send to WhatsApp
    try:
        api_response = await send_to_whatsapp(image_base64, caption, phone=phone)
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


@app.post("/user")
async def create_user(
    logo: UploadFile = File(...),
    phone: str = Form(...),
    mail: str = Form(...),
    website: str = Form(...),
):
    """
    Create a new user (user) with logo and contact details.
    """
    if not MONGO_URI:
        raise HTTPException(status_code=500, detail="MONGO_URI not configured")

    try:
        logo_content = await logo.read()
        try:
            img = Image.open(io.BytesIO(logo_content))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img = img.resize((150, 150), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img.save(output, format="PNG")
            logo_content = output.getvalue()
        except Exception as img_err:
            raise HTTPException(
                status_code=400, detail=f"Invalid image file: {str(img_err)}"
            )

        user_data = {
            "phone": phone,
            "mail": mail,
            "website": website,
            "logo": logo_content,
            "logo_filename": logo.filename,
            "created_at": datetime.now(),
        }

        result = await collection.insert_one(user_data)

        return {
            "status": "success",
            "message": "User created successfully",
            "id": str(result.inserted_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user")
async def list_users():
    """List all users (excluding binary logo for performance)."""
    cursor = collection.find({}, {"logo": 0})
    users = []
    async for doc in cursor:
        users.append(serialize_doc(doc))
    return users


@app.get("/user/{user_id}")
async def get_user(user_id: str):
    """Get a specific user's details including base64 logo."""
    try:
        doc = await collection.find_one({"_id": ObjectId(user_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="User not found")
        return serialize_doc(doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid User ID or query failed")


@app.put("/user/{user_id}")
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
            img = Image.open(io.BytesIO(logo_content))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img = img.resize((150, 150), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img.save(output, format="PNG")
            update_data["logo"] = output.getvalue()
            update_data["logo_filename"] = logo.filename
        except Exception as img_err:
            raise HTTPException(
                status_code=400, detail=f"Invalid image file: {str(img_err)}"
            )

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        result = await collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "success", "message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid User ID or update failed")


@app.delete("/user/{user_id}")
async def delete_user(user_id: str):
    """Delete a user."""
    try:
        result = await collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "success", "message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid User ID or delete failed")


@app.post("/distribute-holiday-post")
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
    users_cursor = collection.find({})
    users = []
    async for user in users_cursor:
        users.append(user)

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
            
            # Wait for a random time under 5 minutes (max 300 seconds) BEFORE sending
            # This ensures that for N users, they are spread out over roughly N * 1-5 minutes.
            if index > 0:
                delay_seconds = random.randint(30, 300) # Minimum 30s to be safe, max 5m
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)