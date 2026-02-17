import time
import random
import os
import sys
import subprocess
import socket
import json
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright


# =============================================================================
# FusionSolar Configuration
# =============================================================================
FUSIONSOLAR_HOST = "intl.fusionsolar.huawei.com"
FUSIONSOLAR_BASE = f"https://{FUSIONSOLAR_HOST}"
LOGIN_URL = FUSIONSOLAR_BASE

PORTAL_HOME = (
    f"{FUSIONSOLAR_BASE}/uniportal/pvmswebsite/assets/build/cloud.html"
    "?app-id=smartpvms&instance-id=smartpvms&zone-id=region-7-075ad9fd-a8fc-46e6-8d88-e829f96a09b7"
    "#/home/list"
)


def fix_dns_resolution():
    """Ensure intl.fusionsolar.huawei.com resolves correctly.
    
    Uses multiple strategies:
    1. Check if system DNS already works
    2. DNS-over-HTTPS via Google (works from anywhere, no tools needed)
    3. DNS-over-HTTPS via Cloudflare (backup)
    4. dig command via Google DNS
    """
    print(f"🔍 Checking DNS resolution for {FUSIONSOLAR_HOST}...")

    # Check if system DNS already works
    try:
        ip = socket.gethostbyname(FUSIONSOLAR_HOST)
        print(f"  ✅ DNS OK: {FUSIONSOLAR_HOST} -> {ip}")
        return
    except socket.gaierror:
        print(f"  ⚠️  System DNS failed for {FUSIONSOLAR_HOST}")

    resolved_ip = None

    # Strategy 1: Google DNS-over-HTTPS (most reliable from GH Actions)
    try:
        print("  🔎 Trying Google DNS-over-HTTPS...")
        url = f"https://dns.google/resolve?name={FUSIONSOLAR_HOST}&type=A"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            answers = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
            if answers:
                resolved_ip = answers[0]
                print(f"  ✅ Google DoH resolved: {resolved_ip}")
    except Exception as e:
        print(f"  ⚠️  Google DoH failed: {e}")

    # Strategy 2: Cloudflare DNS-over-HTTPS
    if not resolved_ip:
        try:
            print("  🔎 Trying Cloudflare DNS-over-HTTPS...")
            url = f"https://cloudflare-dns.com/dns-query?name={FUSIONSOLAR_HOST}&type=A"
            req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                answers = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
                if answers:
                    resolved_ip = answers[0]
                    print(f"  ✅ Cloudflare DoH resolved: {resolved_ip}")
        except Exception as e:
            print(f"  ⚠️  Cloudflare DoH failed: {e}")

    # Strategy 3: dig command
    if not resolved_ip:
        try:
            print("  🔎 Trying dig @8.8.8.8...")
            result = subprocess.run(
                ["dig", "+short", FUSIONSOLAR_HOST, "@8.8.8.8"],
                capture_output=True, text=True, timeout=10
            )
            ips = [line.strip() for line in result.stdout.strip().split('\n')
                   if line.strip() and not line.strip().endswith('.')]
            if ips:
                resolved_ip = ips[0]
                print(f"  ✅ dig resolved: {resolved_ip}")
        except Exception as e:
            print(f"  ⚠️  dig failed: {e}")

    if not resolved_ip:
        print("  ❌ All DNS resolution strategies failed!")
        print("  💡 Check if intl.fusionsolar.huawei.com is accessible from this network")
        sys.exit(1)

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
        print(f"  ❌ Could not update /etc/hosts: {e}")
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
            # Step 2: Enter username
            # =========================================================
            print("👤 Step 2: Entering username...")
            username_field = page.get_by_role("textbox", name="Username or email")
            username_field.wait_for(state="visible", timeout=30000)
            username_field.fill(username)
            human_delay(2, 4)

            # =========================================================
            # Step 3: Enter password
            # =========================================================
            print("🔑 Step 3: Entering password...")
            password_field = page.get_by_role("textbox", name="Password")
            password_field.click()
            password_field.fill(password)
            human_delay(2, 4)

            # =========================================================
            # Step 4: Click Log In
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
            # Step 5: Navigate directly to portal
            # Auth cookies are set from login, go straight there
            # =========================================================
            print("🏠 Step 5: Navigating to portal...")
            page.goto(PORTAL_HOME, wait_until="networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(page)

            current_url = page.url
            print(f"📍 Portal: {current_url[:100]}")
            page.screenshot(path="03_portal_home.png", full_page=True)
            print("📸 Portal home screenshot saved")

            # Check if we actually reached the portal or got redirected to login
            if "/login/" in current_url and "/uniportal/" not in current_url:
                print("⚠️  Redirected back to login - auth may have failed")
                print("📋 Cookies:")
                for cookie in context.cookies():
                    print(f"    {cookie['name']}: {cookie['value'][:20]}... (domain: {cookie['domain']})")
                raise Exception("Login did not establish valid session - redirected back to login page")

            # =========================================================
            # Step 6: Search for Nautica
            # =========================================================
            print("🔎 Step 6: Searching for Nautica...")
            search_field = page.get_by_role("textbox", name="Plant name")
            search_field.wait_for(state="visible", timeout=30000)
            search_field.click()
            human_delay(1, 2)
            type_human_like(search_field, "Nautica")
            human_delay(2, 3)

            page.get_by_role("button", name="Search").click()
            page.wait_for_load_state("networkidle", timeout=30000)
            human_delay(5, 8)

            # =========================================================
            # Step 7: Click Nautica Shopping Centre
            # =========================================================
            print("🏢 Step 7: Selecting Nautica Shopping Centre...")
            page.get_by_role("link", name="Nautica Shopping Centre").click()
            page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(page)

            page.screenshot(path="04_nautica_station.png", full_page=True)
            print("📸 Nautica station screenshot saved")

            # =========================================================
            # Step 8: Click Report Management
            # =========================================================
            print("📊 Step 8: Opening Report Management...")
            page.get_by_text("Report Management").click()
            page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(page)

            page.screenshot(path="05_report_page.png", full_page=True)
            print("📸 Report page screenshot saved")

            # =========================================================
            # Step 9: Export report
            # =========================================================
            print("📤 Step 9: Clicking Export...")
            page.get_by_role("button", name="Export").click()
            human_delay(5, 8)

            # =========================================================
            # Step 10: Download the file
            # =========================================================
            print("💾 Step 10: Downloading file...")
            with page.expect_download(timeout=30000) as download_info:
                page.get_by_title("Download").first.click()
            download = download_info.value

            # Save to data directory
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)

            download_path = data_dir / "nautica_raw.xlsx"
            download.save_as(download_path)
            print(f"✅ File downloaded to: {download_path}")

            # =========================================================
            # Step 11: Close dialog
            # =========================================================
            print("✖️  Step 11: Closing dialog...")
            page.get_by_role("button", name="Close").click()
            human_delay(2, 4)

            print("✅ Download completed successfully!")

        except Exception as error:
            print(f"❌ Error during download: {error}")
            print(f"📍 URL: {page.url[:100]}")

            try:
                page.screenshot(path="error_screenshot.png", full_page=True)
                print("📸 Error screenshot saved")
                Path("error_page.html").write_text(page.content())
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
