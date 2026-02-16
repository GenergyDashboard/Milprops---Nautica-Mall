import time
import random
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


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


def download_nautica_data():
    """Download Nautica Shopping Centre data from FusionSolar"""
    
    print("🚀 Starting Nautica Shopping Centre data download...")
    
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
        
        # Create context with realistic settings (like 1st Ave scraper)
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
            # Step 1: Navigate to FusionSolar login
            print("📱 Step 1: Navigating to FusionSolar login...")
            page.goto("https://intl.fusionsolar.huawei.com/pvmswebsite/login/build/index.html",
                     wait_until="networkidle",
                     timeout=60000)
            human_delay(5, 8)
            random_mouse_movement(page)
            
            print(f"📍 Current URL: {page.url}")
            
            # Step 2: Fill in username (character by character for human-like behavior)
            print("👤 Step 2: Entering username...")
            username_field = page.get_by_role("textbox", name="Username or email")
            username_field.wait_for(state="visible", timeout=30000)
            username_field.click()
            human_delay(1, 2)
            random_mouse_movement(page)
            
            # Type character by character
            for char in username:
                username_field.type(char, delay=random.randint(50, 150))
            
            human_delay(5, 8)
            random_mouse_movement(page)
            
            # Step 3: Fill in password (character by character)
            print("🔑 Step 3: Entering password...")
            password_field = page.get_by_role("textbox", name="Password")
            password_field.click()
            human_delay(1, 2)
            random_mouse_movement(page)
            
            # Type character by character
            for char in password:
                password_field.type(char, delay=random.randint(50, 150))
            
            human_delay(5, 8)
            random_mouse_movement(page)
            
            # Step 4: Click login button
            print("🔐 Step 4: Clicking login button...")
            page.locator("#btn_outerverify").click()
            
            print("  ⏳ Waiting for login to complete...")
            page.wait_for_load_state("networkidle", timeout=60000)
            human_delay(7, 10)
            random_mouse_movement(page)
            
            print(f"📍 After login URL: {page.url}")
            
            # Step 5: Navigate to Reports
            print("📊 Step 5: Opening Reports menu...")
            page.locator("#pvmsReport").click()
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
                print(f"📸 Screenshot saved to {screenshot_path}")
            except Exception as screenshot_error:
                print(f"⚠️  Could not take screenshot: {screenshot_error}")
            
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
