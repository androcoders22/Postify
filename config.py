"""
Postify Configuration Module
All application settings, API keys, and prompt templates.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== API KEYS ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# ==================== FILE PATHS ====================
CSV_FILE_PATH = "holidays.csv"
OVERLAY_IMAGE_PATH = "overlay.png"
LOGO_IMAGE_PATH = "logo.png"
FONT_PATH = "GoogleSans_17pt-SemiBold.ttf"

# ==================== API ENDPOINTS ====================
SEND_MEDIA_URL = "https://fast.meteor-fitness.com/send-media?type=base64"
DEFAULT_PHONE_NUMBER = "8299396255"

# ==================== GEMINI MODELS ====================
GEMINI_TEXT_MODEL = "gemini-flash-latest"
GEMINI_IMAGE_MODEL = "gemini-3-pro-image-preview"

# ==================== IMAGE SETTINGS ====================
IMAGE_SIZE = 1024
LOGO_SIZE = 120
LOGO_PADDING = 20
USER_LOGO_SIZE = 150

# ==================== FOOTER SETTINGS ====================
DEFAULT_FOOTER_TEXT = "+91 8299396255   |   ANDROCODERS21@GMAIL.COM   |   ANDROCODERS.IN"
FOOTER_ELEVATION = 40
FOOTER_FONT_SIZE = 24
FOOTER_TEXT_COLOR = (255, 255, 255)  # White text

# ==================== PROMPT TEMPLATES ====================
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
A refined English calligraphy greeting such as "Happy {holiday}," rendered in a sophisticated script. The lettering has a flat metallic or gold-foil appearance with natural light reflections and soft highlights, integrated directly into the scene rather than embossed or extruded. It should feel elegant, premium, and readable at feed scale.

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
