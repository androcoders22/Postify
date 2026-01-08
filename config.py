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
STRUCTURED_OUTPUT_PROMPT = """You are a creative visual designer. For the holiday "{holiday}", produce a JSON object with exactly two keys: "prompt" and "caption".

IMPORTANT:

"prompt" must be a single, flowing, narrative image-generation paragraph suitable for a text-to-image model.

Output valid JSON only.

What the image-generation prompt must describe:
Overall scene:
A premium gallery-ready printable image with a graphic-design / flat-illustration aesthetic (welcoming, festive slightly glowing), not photorealistic. This is a full-canvas artwork that bleeds to all edges with absolutely no borders, margins, or white space around it. Aim for smooth shapes, subtle gradients, clean outlines, tasteful texture hints, and a printed/graphic feel rather than photographic materials.

Composition:
A balanced left–right layout designed for a square canvas. Elegant English calligraphic greeting text appears on the LEFT, while a cohesive symbolic illustration appears on the RIGHT. Both sides must live in the same continuous visual that extends fully to all four edges. prompt will always end with '(full-bleed gallery image, no borders, no margins, no white space around edges)'

LEFT — greeting:
A refined English calligraphy greeting for {holiday}, set in a sophisticated script. The lettering has a flat metallic or gold-foil appearance with subtle, graphic highlights and minimal surface texture — integrated directly into the scene (flat and printed look, not embossed, extruded, or photographic). It must read clearly and feel premium and elegant.

RIGHT — Illustration:
A harmonious grounded still-life made of two to four cohesive, symbolic elements representing {holiday} (arranged on a subtle tabletop or ground plane so they sit naturally together). Elements must be graphic/illustrated (stylized bow & arrow, diya and marigolds, crescent and lantern, tree and ornaments, etc., depending on the holiday) with clean shapes, clear silhouettes, and crisp graphic shadows. Ensure elements interact subtly and feel intentionally arranged — not floating or isolated.

Background & environment:
A rich background with ornamental patterning or decorative motifs blended at roughly 40% opacity so it unifies the composition without overpowering it. Background treatments should read as printed/graphic texture (subtle pattern), not photographic. The background must fill the entire canvas completely to all four edges with no white space, borders, or margins whatsoever.

Depth, focus & lighting:
Keep full graphic clarity across the scene: use deep apparent depth while maintaining sharpness and detail on both typography and symbolic elements. Lighting should be soft, diffused, stylized—using crisp, vector-friendly shadows and gentle rim highlights to define edges. Avoid photographic bokeh.

Style:
Premium, sleek, and gallery-ready printable artwork. Fine materials suggested through graphic cues, balanced contrast, warm inviting mood, and overall visual cohesion. This is a complete canvas-filling image with no frame, no mat, no borders. Strictly avoid logos, watermarks, footer/contact text, UI elements, white margins, white borders, white padding, outer frames, stamped footers, or any visible branding. The artwork must fill 100% of the canvas edge-to-edge. Do not produce framed panels, inset cards, or any composition that isolates left and right as separate framed tiles.

Output JSON schema:
Produce only valid JSON with exactly two keys: "prompt" and "caption". The "prompt" value must be a single paragraph describing the full square left-right graphic illustration scene (as above) and must not contain meta instructions or bullet lists. The "caption" value should be a short social caption (one or two sentences) that may include emojis.

Example structure (must match this format exactly):
{{
"prompt": "<single-paragraph image-generation prompt for a non-photoreal, graphic-designed left-right square gallery image for {holiday}>",
"caption": "<short social caption with emojis>"
}}
"""