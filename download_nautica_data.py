import time
import random
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def random_wait():
    """Wait for a random interval between 1 and 5 seconds"""
    time.sleep(random.uniform(1, 5))


def download_nautica_data():
    """Download Nautica Shopping Centre data from FusionSolar"""
    
    print("Starting Nautica Shopping Centre data download...")
    
    # Get credentials from environment
    username = os.environ.get('FUSIONSOLAR_USERNAME')
    password = os.environ.get('FUSIONSOLAR_PASSWORD')
    
    if not username or not password:
        print("ERROR: FUSIONSOLAR_USERNAME and FUSIONSOLAR_PASSWORD must be set")
        sys.exit(1)
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Step 1: Navigate to FusionSolar login
            print("Step 1: Navigating to FusionSolar login...")
            page.goto("https://intl.fusionsolar.huawei.com/pvmswebsite/login/build/index.html")
            random_wait()
            
            # Step 2: Fill in username
            print("Step 2: Entering username...")
            page.get_by_role("textbox", name="Username or email").click()
            random_wait()
            page.get_by_role("textbox", name="Username or email").fill(username)
            random_wait()
            
            # Step 3: Fill in password
            print("Step 3: Entering password...")
            page.get_by_role("textbox", name="Password").click()
            random_wait()
            page.get_by_role("textbox", name="Password").fill(password)
            random_wait()
            
            # Step 4: Click login button
            print("Step 4: Clicking login button...")
            page.locator("#btn_outerverify").click()
            random_wait()
            
            # Step 5: Navigate to Reports
            print("Step 5: Opening Reports menu...")
            page.locator("#pvmsReport").click()
            random_wait()
            
            # Step 6: Click Plant Report
            print("Step 6: Opening Plant Report...")
            page.get_by_role("link", name="Plant Report").click()
            random_wait()
            
            # Step 7: Click on Nautica Shopping Centre
            print("Step 7: Selecting Nautica Shopping Centre...")
            page.get_by_text("Nautica Shopping Centre").click()
            random_wait()
            
            # Step 8: Export report
            print("Step 8: Clicking Export...")
            page.get_by_role("button", name="Export").click()
            random_wait()
            
            # Step 9: Download the file
            print("Step 9: Downloading file...")
            with page.expect_download() as download_info:
                page.get_by_title("Download").first.click()
            download = download_info.value
            
            # Save to data directory
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            download_path = data_dir / "nautica_raw.xlsx"
            download.save_as(download_path)
            print(f"✓ File downloaded to: {download_path}")
            
            random_wait()
            
            # Step 10: Close the dialog
            print("Step 10: Closing export dialog...")
            page.get_by_role("button", name="Close").click()
            
            print("✓ Download completed successfully!")
            
        except Exception as error:
            print(f"✗ Error during download: {error}")
            
            # Take screenshot for debugging
            try:
                screenshot_path = Path("error_screenshot.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"Screenshot saved to {screenshot_path}")
            except Exception as screenshot_error:
                print(f"Could not take screenshot: {screenshot_error}")
            
            raise
            
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    try:
        download_nautica_data()
    except Exception as e:
        print(f"Script failed: {e}")
        sys.exit(1)
