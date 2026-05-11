import asyncio
from playwright.async_api import async_playwright
import os
import subprocess
import time

async def verify():
    # Start the frontend server
    proc = subprocess.Popen(["npm", "start"], cwd="frontend", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Starting frontend server...")
    time.sleep(15) # Wait for it to start

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto("http://localhost:3000", timeout=60000)
            print("Page loaded successfully")

            # Check for initial light/dark state
            is_dark = await page.evaluate("document.documentElement.classList.contains('dark')")
            print(f"Initial dark mode: {is_dark}")

            await page.screenshot(path="initial_load.png")
            print("Saved initial_load.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

    proc.terminate()

if __name__ == "__main__":
    asyncio.run(verify())
