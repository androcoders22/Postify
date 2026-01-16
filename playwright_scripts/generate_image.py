import sys
import base64
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = Path(__file__).parent / "browser_profile"

def main():
    prompt = sys.stdin.read().strip()

    if not prompt:
        print("[playwright] ERROR: No prompt provided via stdin", file=sys.stderr)
        sys.exit(1)

    print(f"[playwright] Received prompt: {prompt}", file=sys.stderr)
    print("[playwright] Opening browser with persistent profile...", file=sys.stderr)

    USER_DATA_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=True,
            args=['--disable-blink-features=AutomationControlled', "--no-sandbox", "--disable-dev-shm-usage"],
            viewport={'width': 1280, 'height': 720},
        )

        page = context.pages[0] if context.pages else context.new_page()

        print("[playwright] Navigating to https://gemini.google.com/app", file=sys.stderr)
        page.goto("https://gemini.google.com/app", wait_until="domcontentloaded")

        print("[playwright] Page loaded!", file=sys.stderr)
        page.wait_for_timeout(2000)

        try:
            print("[playwright] Looking for 'Create image' button...", file=sys.stderr)
            create_image_btn = page.locator('button:has-text("Create Image")')
            create_image_btn.wait_for(state="visible", timeout=10000)

            print("[playwright] Found button! Clicking...", file=sys.stderr)
            create_image_btn.click()
            print("[playwright] Button clicked successfully!", file=sys.stderr)

            page.wait_for_timeout(1000)

            print("[playwright] Looking for input field...", file=sys.stderr)
            input_field = page.locator('[aria-label="Enter a prompt here"]')
            input_field.wait_for(state="visible", timeout=10000)

            print("[playwright] Found input field! Focusing...", file=sys.stderr)
            input_field.click()
            print("[playwright] Input field focused!", file=sys.stderr)

            page.wait_for_timeout(500)

            print(f"[playwright] Typing prompt...", file=sys.stderr)
            input_field.fill(prompt)
            print("[playwright] Prompt entered!", file=sys.stderr)

            page.wait_for_timeout(500)

            print("[playwright] Looking for send button...", file=sys.stderr)
            send_button = page.locator('mat-icon[fonticon="send"]')
            send_button.wait_for(state="visible", timeout=10000)

            print("[playwright] Found send button! Clicking...", file=sys.stderr)
            send_button.click()
            print("[playwright] Send button clicked!", file=sys.stderr)

            print("[playwright] Waiting for image to generate...", file=sys.stderr)
            page.wait_for_timeout(5000)

            image_locator = page.locator('img.image.animate.loaded')
            image_locator.wait_for(state="visible", timeout=60000)

            image_url = image_locator.get_attribute('src')
            print(f"[playwright] Image generated! URL: {image_url}", file=sys.stderr)

            response = page.request.get(image_url)
            image_bytes = response.body()

            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            print(image_base64)

        except Exception as e:
            print(f"[playwright] Error: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            try:
                context.close()
            except:
                pass

if __name__ == "__main__":
    main()