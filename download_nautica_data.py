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
LOGIN_URL = FUSIONSOLAR_BASE

PORTAL_HOME = (
    f"{FUSIONSOLAR_BASE}/uniportal/pvmswebsite/assets/build/cloud.html"
    "?app-id=smartpvms&instance-id=smartpvms&zone-id=region-7-075ad9fd-a8fc-46e6-8d88-e829f96a09b7"
    "#/home/list"
)

# Known fallback IP (resolved via Google DNS from a working network)
FALLBACK_IP = "119.8.229.117"


def fix_dns_resolution():
    """Ensure intl.fusionsolar.huawei.com resolves - fix /etc/hosts if needed"""
    print(f"🔍 Checking DNS resolution for {FUSIONSOLAR_HOST}...")

    try:
        ip = socket.gethostbyname(FUSIONSOLAR_HOST)
        print(f"  ✅ DNS OK: {FUSIONSOLAR_HOST} -> {ip}")
        return
    except socket.gaierror:
        print(f"  ⚠️  DNS resolution failed for {FUSIONSOLAR_HOST}")

    # Try dig via Google DNS
    resolved_ip = None
    try:
        result = subprocess.run(
            ["dig", "+short", FUSIONSOLAR_HOST, "@8.8.8.8"],
            capture_output=True, text=True, timeout=10
        )
        ips = [line.strip() for line in result.stdout.strip().split('\n')
               if line.strip() and not line.strip().endswith('.')]
        if ips:
            resolved_ip = ips[0]
            print(f"  ✅ Resolved via Google DNS: {resolved_ip}")
    except Exception:
        pass

    if not resolved_ip:
        resolved_ip = FALLBACK_IP
        print(f"  ⚠️  Using fallback IP: {resolved_ip}")

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
        print(f"  ❌ DNS still failing")
        sys.exit(1)


def human_delay(min_seconds=3, max_seconds=7):
    delay = random.uniform(min_seconds, max_seconds)
    print(f"  ⏳ Waiting {delay:.1f} seconds...")
    time.sleep(delay)


def random_mouse_movement(page):
    try:
        vs = page.viewport_size
        if vs:
            page.mouse.move(random.randint(100, vs['width'] - 100),
                            random.randint(100, vs['height'] - 100))
    except:
        pass


def type_human_like(field, text):
    for char in text:
        field.type(char, delay=random.randint(50, 150))


def inspect_page(page, label=""):
    """Dump all visible interactive elements for selector debugging"""
    print(f"\n{'='*60}")
    print(f"🔍 PAGE INSPECTION{' - ' + label if label else ''}")
    print(f"📍 URL: {page.url}")
    print(f"📄 Title: {page.title()}")
    print(f"{'='*60}")

    # Textboxes / inputs
    print("\n📝 TEXTBOXES (role=textbox):")
    try:
        textboxes = page.get_by_role("textbox").all()
        for i, tb in enumerate(textboxes):
            try:
                visible = tb.is_visible(timeout=1000)
                name = tb.get_attribute("name") or ""
                placeholder = tb.get_attribute("placeholder") or ""
                aria = tb.get_attribute("aria-label") or ""
                input_type = tb.get_attribute("type") or ""
                print(f"  [{i}] visible={visible} name='{name}' placeholder='{placeholder}' aria='{aria}' type='{input_type}'")
            except:
                print(f"  [{i}] (could not inspect)")
    except:
        print("  (none found)")

    # All input elements
    print("\n📝 ALL INPUTS (input tag):")
    try:
        inputs = page.locator("input").all()
        for i, inp in enumerate(inputs):
            try:
                visible = inp.is_visible(timeout=1000)
                name = inp.get_attribute("name") or ""
                placeholder = inp.get_attribute("placeholder") or ""
                input_type = inp.get_attribute("type") or ""
                input_id = inp.get_attribute("id") or ""
                cls = inp.get_attribute("class") or ""
                print(f"  [{i}] visible={visible} id='{input_id}' name='{name}' placeholder='{placeholder}' type='{input_type}' class='{cls[:50]}'")
            except:
                print(f"  [{i}] (could not inspect)")
    except:
        print("  (none found)")

    # Buttons
    print("\n🔘 BUTTONS:")
    try:
        buttons = page.get_by_role("button").all()
        for i, btn in enumerate(buttons):
            try:
                visible = btn.is_visible(timeout=1000)
                text = btn.text_content() or ""
                print(f"  [{i}] visible={visible} text='{text.strip()[:60]}'")
            except:
                print(f"  [{i}] (could not inspect)")
    except:
        print("  (none found)")

    # Links
    print("\n🔗 LINKS:")
    try:
        links = page.get_by_role("link").all()
        for i, link in enumerate(links):
            try:
                visible = link.is_visible(timeout=1000)
                text = link.text_content() or ""
                href = link.get_attribute("href") or ""
                if visible:
                    print(f"  [{i}] text='{text.strip()[:60]}' href='{href[:80]}'")
            except:
                pass
    except:
        print("  (none found)")

    # Key text content on page
    print("\n📋 KEY TEXT VISIBLE ON PAGE:")
    try:
        body_text = page.locator("body").text_content() or ""
        # Get unique meaningful phrases
        words = [w.strip() for w in body_text.split('\n') if w.strip() and len(w.strip()) > 3]
        seen = set()
        for w in words[:50]:
            short = w[:80]
            if short not in seen:
                seen.add(short)
                print(f"  '{short}'")
    except:
        print("  (could not read)")

    print(f"{'='*60}\n")


def download_nautica_data():
    """Download Nautica Shopping Centre data from FusionSolar"""

    print("🚀 Starting Nautica Shopping Centre data download...")
    print(f"🌐 Target: {LOGIN_URL}")

    fix_dns_resolution()

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

            # Inspect what's on the page after login
            inspect_page(page, "AFTER LOGIN")

            # =========================================================
            # Step 5: Navigate to portal
            # =========================================================
            print("🏠 Step 5: Navigating to portal...")
            page.goto(PORTAL_HOME, wait_until="networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(page)

            print(f"📍 Portal: {page.url[:100]}")
            page.screenshot(path="03_portal_home.png", full_page=True)

            # Inspect what's on the portal page
            inspect_page(page, "PORTAL HOME")

            # =========================================================
            # Step 6: Search for Nautica
            # Try multiple selector strategies based on inspection
            # =========================================================
            print("🔎 Step 6: Searching for Nautica...")

            search_field = None
            search_strategies = [
                ("role textbox 'Plant name'", lambda: page.get_by_role("textbox", name="Plant name")),
                ("placeholder 'Plant name'", lambda: page.locator("input[placeholder*='Plant name']").first),
                ("placeholder 'plant'", lambda: page.locator("input[placeholder*='plant']").first),
                ("placeholder 'search'", lambda: page.locator("input[placeholder*='search' i]").first),
                ("placeholder 'Search'", lambda: page.locator("input[placeholder*='Search']").first),
                ("role searchbox", lambda: page.get_by_role("searchbox").first),
                ("visible text input", lambda: page.locator("input[type='text']:visible").first),
                ("any visible input", lambda: page.locator("input:visible").first),
            ]

            for name, strategy in search_strategies:
                try:
                    field = strategy()
                    if field.is_visible(timeout=3000):
                        search_field = field
                        print(f"  ✅ Found search field with: {name}")
                        break
                except:
                    continue

            if not search_field:
                print("  ❌ Could not find any search/input field!")
                raise Exception("No search field found on portal page - check inspection output above")

            search_field.click()
            human_delay(1, 2)
            type_human_like(search_field, "Nautica")
            human_delay(2, 3)

            # Try to click Search button
            try:
                page.get_by_role("button", name="Search").click()
            except:
                # Maybe there's a different button or it auto-searches
                try:
                    page.locator("button:has-text('Search')").first.click()
                except:
                    # Press Enter as fallback
                    search_field.press("Enter")

            page.wait_for_load_state("networkidle", timeout=30000)
            human_delay(5, 8)

            # =========================================================
            # Step 7: Click Nautica Shopping Centre
            # =========================================================
            print("🏢 Step 7: Selecting Nautica Shopping Centre...")
            try:
                page.get_by_role("link", name="Nautica Shopping Centre").click()
            except:
                # Fallback: find by text
                page.get_by_text("Nautica Shopping Centre").first.click()

            page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(page)

            page.screenshot(path="04_nautica_station.png", full_page=True)

            # =========================================================
            # Step 8: Click Report Management
            # =========================================================
            print("📊 Step 8: Opening Report Management...")
            page.get_by_text("Report Management").click()
            page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(page)

            page.screenshot(path="05_report_page.png", full_page=True)

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
