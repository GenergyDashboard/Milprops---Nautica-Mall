import time
import random
import os
import sys
import subprocess
import socket
from pathlib import Path
from playwright.sync_api import sync_playwright


# =============================================================================
# FusionSolar Configuration
# =============================================================================
FUSIONSOLAR_HOST = "intl.fusionsolar.huawei.com"
FUSIONSOLAR_BASE = f"https://{FUSIONSOLAR_HOST}"

# Login URL - just the base domain, FusionSolar redirects to login page
LOGIN_URL = FUSIONSOLAR_BASE

# Portal home URL (navigated to after login)
PORTAL_HOME = (
    f"{FUSIONSOLAR_BASE}/uniportal/pvmswebsite/assets/build/cloud.html"
    "?app-id=smartpvms&instance-id=smartpvms&zone-id=region-7-075ad9fd-a8fc-46e6-8d88-e829f96a09b7"
    "#/home/list"
)

# Known fallback IPs when DNS fails on GitHub Actions runners
FALLBACK_IPS = ["119.8.229.117"]


def fix_dns_resolution():
    """Ensure intl.fusionsolar.huawei.com resolves - fix /etc/hosts if needed"""
    print(f"🔍 Checking DNS resolution for {FUSIONSOLAR_HOST}...")

    try:
        ip = socket.gethostbyname(FUSIONSOLAR_HOST)
        print(f"  ✅ DNS OK: {FUSIONSOLAR_HOST} -> {ip}")
        return
    except socket.gaierror:
        print(f"  ⚠️  DNS resolution failed for {FUSIONSOLAR_HOST}")

    # Try resolving via Google DNS
    resolved_ip = None
    try:
        result = subprocess.run(
            ["dig", "+short", FUSIONSOLAR_HOST, "@8.8.8.8"],
            capture_output=True, text=True, timeout=10
        )
        ips = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        if ips:
            resolved_ip = ips[0]
            print(f"  ✅ Resolved via Google DNS: {resolved_ip}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  ⚠️  dig not available or timed out")

    if not resolved_ip:
        resolved_ip = FALLBACK_IPS[0]
        print(f"  ⚠️  Using known fallback IP: {resolved_ip}")

    # Write to /etc/hosts
    hosts_entry = f"{resolved_ip} {FUSIONSOLAR_HOST}\n"
    try:
        with open("/etc/hosts", "r") as f:
            if FUSIONSOLAR_HOST in f.read():
                print("  ℹ️  Host entry already exists")
                return

        result = subprocess.run(
            ["sudo", "tee", "-a", "/etc/hosts"],
            input=hosts_entry, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print(f"  ✅ Added to /etc/hosts: {hosts_entry.strip()}")
        else:
            with open("/etc/hosts", "a") as f:
                f.write(hosts_entry)
            print(f"  ✅ Added to /etc/hosts (direct): {hosts_entry.strip()}")
    except Exception as e:
        print(f"  ❌ Could not fix DNS: {e}")
        sys.exit(1)

    # Verify
    try:
        ip = socket.gethostbyname(FUSIONSOLAR_HOST)
        print(f"  ✅ DNS now resolves: {FUSIONSOLAR_HOST} -> {ip}")
    except socket.gaierror:
        print(f"  ❌ DNS still failing after /etc/hosts fix")
        sys.exit(1)


def human_delay(min_seconds=3, max_seconds=7):
    """Random delay to mimic human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    print(f"  ⏳ Waiting {delay:.1f} seconds...")
    time.sleep(delay)


def random_mouse_movement(page):
    """Simulate natural mouse movement"""
    try:
        viewport_size = page.viewport_size
        if viewport_size:
            x = random.randint(100, viewport_size['width'] - 100)
            y = random.randint(100, viewport_size['height'] - 100)
            page.mouse.move(x, y)
    except:
        pass


def type_human_like(field, text):
    """Type text character by character with random delays"""
    for char in text:
        field.type(char, delay=random.randint(50, 150))


def download_nautica_data():
    """Download Nautica Shopping Centre data from FusionSolar"""

    print("🚀 Starting Nautica Shopping Centre data download...")
    print(f"🌐 Target: {LOGIN_URL}")

    # Fix DNS before anything else
    fix_dns_resolution()

    # Get credentials from environment
    username = os.environ.get('FUSIONSOLAR_USERNAME')
    password = os.environ.get('FUSIONSOLAR_PASSWORD')

    if not username or not password:
        print("❌ ERROR: FUSIONSOLAR_USERNAME and FUSIONSOLAR_PASSWORD must be set")
        sys.exit(1)

    print(f"🔐 Using username: {username[:4]}***")

    with sync_playwright() as playwright:
        print("🌐 Launching browser...")

        browser = playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
            ]
        )

        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='Africa/Johannesburg',
        )

        # Hide webdriver detection
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()
        portal_page = None  # Will be set if a popup opens

        try:
            # =========================================================
            # Step 1: Navigate to FusionSolar
            # =========================================================
            print("📱 Step 1: Navigating to FusionSolar...")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(page)

            print(f"📍 Landed on: {page.url[:100]}")
            page.screenshot(path="01_login_page.png", full_page=True)
            print("📸 Login page screenshot saved")

            # =========================================================
            # Step 2: Enter username (from recording)
            # =========================================================
            print("👤 Step 2: Entering username...")
            username_field = page.get_by_role("textbox", name="Username or email")
            username_field.wait_for(state="visible", timeout=30000)
            username_field.fill(username)
            human_delay(2, 4)

            # =========================================================
            # Step 3: Enter password (from recording)
            # =========================================================
            print("🔑 Step 3: Entering password...")
            password_field = page.get_by_role("textbox", name="Password")
            password_field.click()
            password_field.fill(password)
            human_delay(2, 4)

            # =========================================================
            # Step 4: Click Log In (from recording)
            # =========================================================
            print("🔓 Step 4: Clicking Log In...")
            page.get_by_text("Log In").click()

            print("  ⏳ Waiting for login to complete...")
            page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(7, 10)

            print(f"📍 After login: {page.url[:100]}")
            page.screenshot(path="02_after_login.png", full_page=True)
            print("📸 After-login screenshot saved")

            # =========================================================
            # Step 5: Get to the portal
            # After login with base URL, we may need to:
            #   a) Click a link that opens a popup (like recording)
            #   b) Already be in the portal (direct redirect)
            #   c) Navigate manually to portal home
            # =========================================================
            print("🔗 Step 5: Getting to portal...")

            current_url = page.url

            if "uniportal" in current_url or "cloud.html" in current_url:
                # Already in portal
                print("  ✅ Already in portal")
                portal_page = page
            else:
                # Try popup approach from the recording
                try:
                    with page.expect_popup(timeout=15000) as popup_info:
                        page.get_by_role("link").nth(2).click()
                        print("  ✅ Clicked link to open portal popup")
                    portal_page = popup_info.value
                    print(f"📍 Popup opened: {portal_page.url[:80]}...")
                except Exception as popup_err:
                    print(f"  ⚠️  Popup approach failed: {popup_err}")

                    # Check if same-tab navigation happened
                    if "uniportal" in page.url or "cloud.html" in page.url:
                        portal_page = page
                        print("  ✅ Portal loaded in same tab")
                    else:
                        # Navigate directly to portal home
                        print("  ℹ️  Navigating directly to portal home...")
                        page.goto(PORTAL_HOME, wait_until="networkidle", timeout=60000)
                        portal_page = page

            portal_page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(5, 8)

            # =========================================================
            # Step 6: Navigate to plant list (from recording)
            # =========================================================
            print("🏠 Step 6: Navigating to plant list...")
            portal_page.goto(PORTAL_HOME, wait_until="networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(portal_page)

            print(f"📍 Portal: {portal_page.url[:80]}...")
            portal_page.screenshot(path="03_portal_home.png", full_page=True)
            print("📸 Portal home screenshot saved")

            # =========================================================
            # Step 7: Search for Nautica (from recording)
            # =========================================================
            print("🔎 Step 7: Searching for Nautica...")
            search_field = portal_page.get_by_role("textbox", name="Plant name")
            search_field.wait_for(state="visible", timeout=30000)
            search_field.click()
            human_delay(1, 2)
            type_human_like(search_field, "Nautica")
            human_delay(2, 3)

            portal_page.get_by_role("button", name="Search").click()
            portal_page.wait_for_load_state("networkidle", timeout=30000)
            human_delay(5, 8)

            # =========================================================
            # Step 8: Click Nautica Shopping Centre (from recording)
            # =========================================================
            print("🏢 Step 8: Selecting Nautica Shopping Centre...")
            portal_page.get_by_role("link", name="Nautica Shopping Centre").click()
            portal_page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(portal_page)

            portal_page.screenshot(path="04_nautica_station.png", full_page=True)
            print("📸 Nautica station screenshot saved")

            # =========================================================
            # Step 9: Click Report Management (from recording)
            # =========================================================
            print("📊 Step 9: Opening Report Management...")
            portal_page.get_by_text("Report Management").click()
            portal_page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(portal_page)

            portal_page.screenshot(path="05_report_page.png", full_page=True)
            print("📸 Report page screenshot saved")

            # =========================================================
            # Step 10: Export report (from recording)
            # =========================================================
            print("📤 Step 10: Clicking Export...")
            portal_page.get_by_role("button", name="Export").click()
            human_delay(5, 8)

            # =========================================================
            # Step 11: Download the file (from recording)
            # =========================================================
            print("💾 Step 11: Downloading file...")
            with portal_page.expect_download(timeout=30000) as download_info:
                portal_page.get_by_title("Download").first.click()
            download = download_info.value

            # Save to data directory
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)

            download_path = data_dir / "nautica_raw.xlsx"
            download.save_as(download_path)
            print(f"✅ File downloaded to: {download_path}")

            # =========================================================
            # Step 12: Close dialog (from recording)
            # =========================================================
            print("✖️  Step 12: Closing export dialog...")
            portal_page.get_by_role("button", name="Close").click()
            human_delay(2, 4)

            print("✅ Download completed successfully!")

        except Exception as error:
            print(f"❌ Error during download: {error}")

            # Screenshot whichever page is active
            capture_page = page
            try:
                if portal_page and not portal_page.is_closed():
                    capture_page = portal_page
                    print(f"📍 Portal URL: {portal_page.url[:100]}")
                else:
                    print(f"📍 Page URL: {page.url[:100]}")
            except:
                pass

            try:
                capture_page.screenshot(path="error_screenshot.png", full_page=True)
                print("📸 Error screenshot saved")
                Path("error_page.html").write_text(capture_page.content())
                print("📄 Page HTML saved")
            except Exception as debug_err:
                print(f"⚠️  Could not capture debug info: {debug_err}")

            raise

        finally:
            human_delay(2, 4)
            context.close()
            browser.close()
            print("🔒 Browser closed")


if __name__ == "__main__":
    try:
        download_nautica_data()
    except Exception as e:
        print(f"❌ Script failed: {e}")
        sys.exit(1)
