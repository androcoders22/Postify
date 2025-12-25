"""
WhatsApp Service - Send media via WhatsApp API.
"""
import httpx
from config import SEND_MEDIA_URL, DEFAULT_PHONE_NUMBER


async def send_to_whatsapp(
    image_base64: str,
    caption: str,
    phone: str = DEFAULT_PHONE_NUMBER
) -> dict:
    """Send the final image to WhatsApp via API."""
    payload = {
        "phone": phone,
        "message": image_base64,
        "caption": caption
    }

    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(SEND_MEDIA_URL, json=payload, timeout=60.0)
        
        # Handle non-JSON responses gracefully
        try:
            return response.json()
        except Exception:
            # API returned non-JSON (empty or text), but request may have succeeded
            return {
                "status": "sent",
                "status_code": response.status_code,
                "raw_response": response.text[:200] if response.text else "empty"
            }

