from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Verify Landing Page
        print("Navigating to Landing Page...")
        page.goto("http://localhost:3000")
        page.wait_for_selector("text=Track Attacks on Your", timeout=10000)
        page.screenshot(path="/home/jules/verification/landing.png")
        print("Landing Page loaded.")

        # Verify Login Page (Lazy Loaded)
        print("Navigating to Login Page...")
        page.goto("http://localhost:3000/login")
        # LoginPage shows AuthModal.
        # We look for some text likely to be in the modal or the page.
        # AuthModal usually has inputs for email/password.
        page.wait_for_selector("input[type='email']", timeout=10000)

        page.screenshot(path="/home/jules/verification/login.png")
        print("Login Page loaded.")

        browser.close()

if __name__ == "__main__":
    if not os.path.exists("/home/jules/verification"):
        os.makedirs("/home/jules/verification")
    run()
