"""
Playwright Image Service

This module provides a thin wrapper to generate images using a Playwright automation
script. The actual Playwright script is intentionally left for the user to implement
(for example under `playwright_scripts/generate_image.py`).

Contract (what this function expects / returns):
- Input: a single string `prompt` describing the image to generate.
- Behavior: calls an external Python script (using the same interpreter) located at
  `playwright_scripts/generate_image.py` and passes the prompt via stdin. The
  external script MUST write a single base64-encoded PNG image to stdout on
  success.
- Output: returns a PIL.Image.Image instance representing the generated image.
- Errors: raises fastapi.HTTPException with helpful instructions when the
  external script is not present or fails.

This keeps the server-side wiring stable while allowing you to implement the
Playwright automation separately as requested.
"""
import io
import os
import sys
import subprocess
import base64
from typing import Optional
from PIL import Image
from fastapi import HTTPException


PLAYWRIGHT_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "playwright_scripts", "generate_image.py")


def _find_python_executable() -> str:
    # Use same interpreter that's running the app
    return sys.executable


def generate_image_playwright(prompt: str, timeout_seconds: int = 120) -> Image.Image:
    """Generate an image by invoking an external Playwright script.

    The external script MUST accept the prompt via stdin (utf-8) and print a
    base64-encoded PNG to stdout on success. If the script returns non-zero or
    produces no output, a helpful HTTPException will be raised.
    """
    if not os.path.exists(PLAYWRIGHT_SCRIPT):
        raise HTTPException(
            status_code=500,
            detail=(
                "Playwright script not found. Expected: 'playwright_scripts/generate_image.py'. "
                "Please create that script which reads a prompt from stdin and writes a base64 PNG to stdout."
            ),
        )

    python_exec = _find_python_executable()

    try:
        proc = subprocess.run(
            [python_exec, PLAYWRIGHT_SCRIPT],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
        )

        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="ignore")
            raise HTTPException(
                status_code=500,
                detail=(
                    "Playwright script failed. "
                    f"Exit code: {proc.returncode}. Stderr: {stderr[:1000]}"
                ),
            )

        output = proc.stdout.strip()
        if not output:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Playwright script produced no output. Ensure it prints a base64-encoded PNG to stdout."
                ),
            )

        # Decode base64 and return a PIL image
        try:
            image_bytes = base64.b64decode(output)
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to decode image from Playwright output: {e}")

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Playwright image generation timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Playwright execution error: {str(e)}")
