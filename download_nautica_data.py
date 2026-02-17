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
LOGIN_URL = f"{FUSIONSOLAR_BASE}/pvmswebsite/login/build/index.html"

# Known fallback IPs for intl.fusionsolar.huawei.com (when DNS fails)
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
    
    # Fall back to known IP
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
        
        # Try with sudo (for GitHub Actions)
        result = subprocess.run(
            ["sudo", "tee", "-a", "/etc/hosts"],
            input=hosts_entry, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print(f"  ✅ Added to /etc/hosts: {hosts_entry.strip()}")
        else:
            # Try direct write (if running as root)
            with open("/etc/hosts", "a") as f:
                f.write(hosts_entry)
            print(f"  ✅ Added to /etc/hosts (direct): {hosts_entry.strip()}")
    except Exception as e:
        print(f"  ❌ Could not fix DNS: {e}")
        print(f"  💡 Manually add to /etc/hosts: {hosts_entry.strip()}")
        sys.exit(1)
    
    # Verify fix
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


def find_username_field(page):
    """Find the username input field using multiple selector strategies"""
    selectors = [
        # New SSO page selectors
        'input[placeholder*="ername"]',          # Matches "Username" or "Username or email"
        'input[placeholder*="mail"]',            # Matches "email"
        '#userAcct',                              # Known SSO field ID
        'input[name="userAcct"]',
        # Old page selectors (fallback)
        'input[placeholder="Username or email"]',
        # Generic fallbacks
        'input[type="text"]:visible',
        'input:not([type="password"]):not([type="hidden"]):visible',
    ]
    
    for selector in selectors:
        try:
            field = page.locator(selector).first
            if field.is_visible(timeout=2000):
                print(f"  ✅ Found username field with: {selector}")
                return field
        except:
            continue
    
    # Last resort: try by role
    try:
        field = page.get_by_role("textbox").first
        if field.is_visible(timeout=2000):
            print("  ✅ Found username field by role")
            return field
    except:
        pass
    
    return None


def find_password_field(page):
    """Find the password input field using multiple selector strategies"""
    selectors = [
        'input[type="password"]:visible',
        '#nsp_password',
        'input[placeholder*="assword"]',
        'input[name="password"]',
    ]
    
    for selector in selectors:
        try:
            field = page.locator(selector).first
            if field.is_visible(timeout=2000):
                print(f"  ✅ Found password field with: {selector}")
                return field
        except:
            continue
    
    return None


def find_login_button(page):
    """Find the login/submit button using multiple selector strategies"""
    selectors = [
        # New SSO page
        '#btn_submit',
        'button:has-text("Log In")',
        'button:has-text("Login")',
        'div.loginBtn',
        # Old page (fallback)
        '#btn_outerverify',
        # Generic
        'button[type="submit"]',
    ]
    
    for selector in selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000):
                print(f"  ✅ Found login button with: {selector}")
                return btn
        except:
            continue
    
    # Try by role
    try:
        btn = page.get_by_role("button", name="Log In")
        if btn.is_visible(timeout=2000):
            print("  ✅ Found login button by role")
            return btn
    except:
        pass
    
    return None


def type_human_like(field, text):
    """Type text character by character with random delays"""
    for char in text:
        field.type(char, delay=random.randint(50, 150))


def download_nautica_data():
    """Download Nautica Shopping Centre data from FusionSolar"""
    
    print("🚀 Starting Nautica Shopping Centre data download...")
    print(f"🌐 Target URL: {LOGIN_URL}")
    
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
        print("🌐 Launching browser with anti-detection measures...")
        
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        # Create context with realistic settings
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
            # Step 1: Navigate to FusionSolar SSO login
            print("📱 Step 1: Navigating to FusionSolar login...")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(page)
            
            print(f"📍 Current URL: {page.url}")
            
            # Take a screenshot of the login page for debugging
            page.screenshot(path="login_page.png", full_page=True)
            print("📸 Login page screenshot saved")
            
            # Step 2: Find and fill username
            print("👤 Step 2: Entering username...")
            username_field = find_username_field(page)
            if not username_field:
                raise Exception("Could not find username field on login page")
            
            username_field.click()
            human_delay(1, 2)
            random_mouse_movement(page)
            type_human_like(username_field, username)
            
            human_delay(5, 8)
            random_mouse_movement(page)
            
            # Step 3: Find and fill password
            print("🔑 Step 3: Entering password...")
            password_field = find_password_field(page)
            if not password_field:
                raise Exception("Could not find password field on login page")
            
            password_field.click()
            human_delay(1, 2)
            random_mouse_movement(page)
            type_human_like(password_field, password)
            
            human_delay(5, 8)
            random_mouse_movement(page)
            
            # Step 4: Click login button
            print("🔓 Step 4: Clicking login button...")
            login_button = find_login_button(page)
            if not login_button:
                raise Exception("Could not find login button on login page")
            
            login_button.click()
            
            print("  ⏳ Waiting for login to complete...")
            page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(7, 10)
            random_mouse_movement(page)
            
            print(f"📍 After login URL: {page.url}")
            
            # Check for login errors
            try:
                error_msg = page.locator('.error-msg, .nsp-error, .login-error').first
                if error_msg.is_visible(timeout=2000):
                    error_text = error_msg.text_content()
                    raise Exception(f"Login failed with error: {error_text}")
            except Exception as e:
                if "Login failed" in str(e):
                    raise
                # No error message found = good
                pass
            
            # Take post-login screenshot
            page.screenshot(path="post_login.png", full_page=True)
            print("📸 Post-login screenshot saved")
            
            # Step 5: Navigate to Reports
            print("📊 Step 5: Opening Reports menu...")
            # Try multiple selectors for the Reports menu
            reports_selectors = [
                '#pvmsReport',
                'text=Report',
                '[data-menu="report"]',
                'a:has-text("Report")',
            ]
            clicked = False
            for sel in reports_selectors:
                try:
                    elem = page.locator(sel).first
                    if elem.is_visible(timeout=3000):
                        elem.click()
                        clicked = True
                        print(f"  ✅ Clicked reports with: {sel}")
                        break
                except:
                    continue
            if not clicked:
                raise Exception("Could not find Reports menu")
            
            human_delay(5, 8)
            random_mouse_movement(page)
            
            # Step 6: Click Plant Report
            print("📋 Step 6: Opening Plant Report...")
            page.get_by_role("link", name="Plant Report").click()
            page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(7, 10)
            random_mouse_movement(page)
            
            # Step 7: Click on Nautica Shopping Centre
            print("🏢 Step 7: Selecting Nautica Shopping Centre...")
            page.get_by_text("Nautica Shopping Centre").click()
            human_delay(6, 9)
            random_mouse_movement(page)
            
            # Step 8: Export report
            print("📤 Step 8: Clicking Export...")
            page.get_by_role("button", name="Export").click()
            human_delay(5, 8)
            random_mouse_movement(page)
            
            # Step 9: Download the file
            print("💾 Step 9: Downloading file...")
            with page.expect_download(timeout=30000) as download_info:
                page.get_by_title("Download").first.click()
            download = download_info.value
            
            # Save to data directory
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            download_path = data_dir / "nautica_raw.xlsx"
            download.save_as(download_path)
            print(f"✅ File downloaded to: {download_path}")
            
            human_delay(2, 4)
            random_mouse_movement(page)
            
            # Step 10: Close the dialog
            print("✖️  Step 10: Closing export dialog...")
            page.get_by_role("button", name="Close").click()
            
            print("✅ Download completed successfully!")
            
        except Exception as error:
            print(f"❌ Error during download: {error}")
            print(f"📍 Last known URL: {page.url if page else 'unknown'}")
            
            # Take screenshot for debugging
            try:
                screenshot_path = Path("error_screenshot.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Error screenshot saved to {screenshot_path}")
                
                # Also dump the page HTML for debugging selectors
                html_path = Path("error_page.html")
                html_path.write_text(page.content())
                print(f"📄 Page HTML saved to {html_path}")
            except Exception as screenshot_error:
                print(f"⚠️  Could not capture debug info: {screenshot_error}")
            
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
