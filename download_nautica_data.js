const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function downloadNauticaData() {
    console.log('Starting Nautica Shopping Centre data download...');
    
    const browser = await chromium.launch({ 
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'] // For CI environments
    });
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
        // Step 1: Navigate to FusionSolar login
        console.log('Step 1: Navigating to FusionSolar...');
        await page.goto('https://intl.fusionsolar.huawei.com/', { 
            waitUntil: 'domcontentloaded',
            timeout: 30000 
        });
        
        // Wait for login form
        await page.waitForSelector('input[type="text"], input[name="username"]', { timeout: 10000 });
        
        // Step 2: Login
        console.log('Step 2: Logging in...');
        await page.fill('input[type="text"], input[name="username"]', process.env.FUSIONSOLAR_USERNAME);
        await page.fill('input[type="password"]', process.env.FUSIONSOLAR_PASSWORD);
        
        // Click login button
        await page.click('text="Log In", button:has-text("Log In")');
        
        // Wait for navigation after login
        console.log('Waiting for login to complete...');
        await page.waitForLoadState('networkidle', { timeout: 20000 });
        await page.waitForTimeout(3000);

        // Step 3: Navigate to plant list
        console.log('Step 3: Navigating to plant list...');
        
        // Try to handle popup or direct navigation
        let plantPage;
        try {
            // Wait for either a popup or navigation
            const popupPromise = page.waitForEvent('popup', { timeout: 5000 });
            
            // Click on link that opens plant list (try different methods)
            await Promise.race([
                page.click('a:nth-of-type(3)'),
                page.click('a[href*="cloud.html"]'),
                page.goto('https://intl.fusionsolar.huawei.com/uniportal/pvmswebsite/assets/build/cloud.html#/home/list')
            ]).catch(() => {});
            
            plantPage = await popupPromise.catch(() => null);
        } catch (e) {
            console.log('No popup detected, using current page...');
        }
        
        // If no popup, use current page or navigate directly
        if (!plantPage) {
            console.log('Navigating directly to plant list...');
            await page.goto('https://intl.fusionsolar.huawei.com/uniportal/pvmswebsite/assets/build/cloud.html#/home/list', {
                waitUntil: 'networkidle',
                timeout: 20000
            });
            plantPage = page;
        }

        await plantPage.waitForLoadState('networkidle');
        await plantPage.waitForTimeout(2000);

        // Step 4: Search for Nautica
        console.log('Step 4: Searching for Nautica Shopping Centre...');
        await plantPage.waitForSelector('input[placeholder*="Plant"], input[name*="plant"]', { timeout: 10000 });
        await plantPage.fill('input[placeholder*="Plant"], input[name*="plant"]', 'Nautica');
        
        // Click search button
        await plantPage.click('button:has-text("Search")');
        await plantPage.waitForTimeout(2000);

        // Step 5: Click on Nautica Shopping Centre
        console.log('Step 5: Opening Nautica Shopping Centre...');
        await plantPage.click('text="Nautica Shopping Centre"');
        await plantPage.waitForTimeout(2000);

        // Step 6: Go to Report Management
        console.log('Step 6: Opening Report Management...');
        await plantPage.click('text="Report Management"');
        await plantPage.waitForTimeout(2000);

        // Step 7: Export report
        console.log('Step 7: Exporting report...');
        await plantPage.click('button:has-text("Export")');
        await plantPage.waitForTimeout(2000);

        // Step 8: Download the file
        console.log('Step 8: Downloading file...');
        const downloadPromise = plantPage.waitForEvent('download', { timeout: 30000 });
        await plantPage.click('[title="Download"], button:has-text("Download")');
        const download = await downloadPromise;
        
        // Save the download
        const downloadPath = path.join(__dirname, 'data', 'nautica_raw.xlsx');
        
        // Ensure data directory exists
        if (!fs.existsSync(path.join(__dirname, 'data'))) {
            fs.mkdirSync(path.join(__dirname, 'data'));
        }
        
        await download.saveAs(downloadPath);
        console.log(`✓ File downloaded to: ${downloadPath}`);

        // Close the export dialog
        await plantPage.click('button:has-text("Close")').catch(() => {});

        console.log('✓ Download completed successfully!');

    } catch (error) {
        console.error('✗ Error during download:', error.message);
        
        // Take a screenshot for debugging
        try {
            await page.screenshot({ path: 'error_screenshot.png', fullPage: true });
            console.log('Screenshot saved to error_screenshot.png');
        } catch (screenshotError) {
            console.error('Could not take screenshot:', screenshotError.message);
        }
        
        throw error;
    } finally {
        await browser.close();
    }
}

// Run the script
downloadNauticaData().catch(error => {
    console.error('Script failed:', error.message);
    process.exit(1);
});
