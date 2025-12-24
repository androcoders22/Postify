"""
Image Service - Image processing and overlay operations.
"""
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from config import (
    IMAGE_SIZE,
    OVERLAY_IMAGE_PATH,
    LOGO_IMAGE_PATH,
    LOGO_SIZE,
    LOGO_PADDING,
    USER_LOGO_SIZE,
    DEFAULT_FOOTER_TEXT,
    FOOTER_ELEVATION,
    FOOTER_FONT_SIZE,
    FOOTER_TEXT_COLOR,
    FONT_PATH,
)


def process_logo(logo_content: bytes) -> bytes:
    """Process and resize a logo image to standard size."""
    img = Image.open(io.BytesIO(logo_content))
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img = img.resize((USER_LOGO_SIZE, USER_LOGO_SIZE), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def overlay_images(
    generated_image: Image.Image,
    logo_data: bytes = None,
    footer_text: str = DEFAULT_FOOTER_TEXT,
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
    logo = None
    if logo_data:
        logo = Image.open(io.BytesIO(logo_data)).convert("RGBA")
    else:
        # Fallback to local default logo if available
        try:
            logo = Image.open(LOGO_IMAGE_PATH).convert("RGBA")
        except Exception:
            pass

    if logo:
        logo = logo.resize((LOGO_SIZE, LOGO_SIZE), Image.Resampling.LANCZOS)
        final_image.paste(logo, (LOGO_PADDING, LOGO_PADDING), logo)

    # Layer 4: Add footer text
    draw = ImageDraw.Draw(final_image)

    try:
        font = ImageFont.truetype(FONT_PATH, FOOTER_FONT_SIZE)
    except (IOError, OSError):
        print(f"Warning: Could not load {FONT_PATH}, falling back to default")
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
    # Convert to RGB if needed (for PNG compatibility with alpha)
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
