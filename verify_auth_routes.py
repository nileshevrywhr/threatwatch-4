from playwright.sync_api import sync_playwright, Page, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    print("Test 1: Unauthenticated access to /feed redirects to /login")
    try:
        # Navigate to /feed
        page.goto("http://localhost:3000/feed")

        # Wait for potential redirect
        page.wait_for_url("**/login", timeout=5000)

        # Check if we are on login page
        assert "/login" in page.url
        print("PASS: Redirected to /login")

        # Verify Login Page content (e.g., check for Sign In text)
        expect(page.get_by_text("Welcome to ThreatWatch")).to_be_visible()
        print("PASS: Login page content visible")

        page.screenshot(path="/home/jules/verification/redirect_to_login.png")

    except Exception as e:
        print(f"FAIL: Test 1 failed: {e}")
        page.screenshot(path="/home/jules/verification/fail_test1.png")

    # Note: Testing "Authenticated access to /login redirects to /feed" is hard without mocking the actual AuthProvider state
    # or being able to login. Since backend is offline, we can't login via UI.
    # However, we can inspect the code logic which we have already done.
    # We can try to verify that IF we were logged in (mocked), it would redirect.
    # But mocking `useAuth` hook in a compiled React app from Playwright is non-trivial without specific test hooks.
    # For now, we rely on the code verification for the authenticated case,
    # and this test confirms the unauthenticated protection works.

    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
