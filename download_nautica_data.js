const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

function randomWait() {
    // Wait for a random interval between 1 and 5 seconds
    return new Promise(resolve => setTimeout(resolve, Math.random() * 4000 + 1000));
}

async function downloadNauticaData() {
    console.log('Starting Nautica Shopping Centre data download...');
    
    const browser = await chromium.launch({ 
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
        // Step 1: Navigate to FusionSolar login page
        console.log('Step 1: Navigating to FusionSolar login...');
        await page.goto('https://intl.fusionsolar.huawei.com/pvmswebsite/login/build/index.html');
        await randomWait();
        
        // Step 2: Fill in username
        console.log('Step 2: Entering username...');
        await page.getByRole('textbox', { name: 'Username or email' }).click();
        await randomWait();
        await page.getByRole('textbox', { name: 'Username or email' }).fill(process.env.FUSIONSOLAR_USERNAME);
        await randomWait();
        
        // Step 3: Fill in password
        console.log('Step 3: Entering password...');
        await page.getByRole('textbox', { name: 'Password' }).click();
        await randomWait();
        await page.getByRole('textbox', { name: 'Password' }).fill(process.env.FUSIONSOLAR_PASSWORD);
        await randomWait();
        
        // Step 4: Click login button (using ID selector like Python script)
        console.log('Step 4: Clicking login button...');
        await page.locator('#btn_outerverify').click();
        await randomWait();
        
        // Step 5: Navigate to Reports
        console.log('Step 5: Opening Reports menu...');
        await page.locator('#pvmsReport').click();
        await randomWait();
        
        // Step 6: Click Plant Report
        console.log('Step 6: Opening Plant Report...');
        await page.getByRole('link', { name: 'Plant Report' }).click();
        await randomWait();
        
        // Step 7: Click on Nautica Shopping Centre
        console.log('Step 7: Selecting Nautica Shopping Centre...');
        await page.getByText('Nautica Shopping Centre').click();
        await randomWait();
        
        // Step 8: Export report
        console.log('Step 8: Clicking Export...');
        await page.getByRole('button', { name: 'Export' }).click();
        await randomWait();
        
        // Step 9: Download the file
        console.log('Step 9: Downloading file...');
        const downloadPromise = page.waitForEvent('download', { timeout: 30000 });
        await page.getByTitle('Download').first.click();
        const download = await downloadPromise;
        
        // Save the download
        const downloadDir = path.join(__dirname, 'data');
        if (!fs.existsSync(downloadDir)) {
            fs.mkdirSync(downloadDir, { recursive: true });
        }
        
        const downloadPath = path.join(downloadDir, 'nautica_raw.xlsx');
        await download.saveAs(downloadPath);
        console.log(`✓ File downloaded to: ${downloadPath}`);
        
        await randomWait();
        
        // Step 10: Close the dialog
        console.log('Step 10: Closing export dialog...');
        await page.getByRole('button', { name: 'Close' }).click();
        
        console.log('✓ Download completed successfully!');

    } catch (error) {
        console.error('✗ Error during download:', error.message);
        console.error('Error stack:', error.stack);
        
        // Take a screenshot for debugging
        try {
            const screenshotPath = path.join(__dirname, 'error_screenshot.png');
            await page.screenshot({ path: screenshotPath, fullPage: true });
            console.log(`Screenshot saved to ${screenshotPath}`);
        } catch (screenshotError) {
            console.error('Could not take screenshot:', screenshotError.message);
        }
        
        throw error;
    } finally {
        await context.close();
        await browser.close();
    }
}

// Run the script
downloadNauticaData().catch(error => {
    console.error('Script failed:', error.message);
    process.exit(1);
});
