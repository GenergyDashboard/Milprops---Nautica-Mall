const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function downloadNauticaData() {
    console.log('Starting Nautica Shopping Centre data download...');
    
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
        // Navigate to login page
        console.log('Navigating to FusionSolar login...');
        await page.goto('https://intl.fusionsolar.huawei.com/pvmswebsite/login/build/index.html#https%3A%2F%2Fintl.fusionsolar.huawei.com%2Funiportal%2Fpvmswebsite%2Fassets%2Fbuild%2Fcloud.html%3Fapp-id%3Dsmartpvms%26instance-id%3Dsmartpvms%26zone-id%3Dregion-7-075ad9fd-a8fc-46e6-8d88-e829f96a09b7%23%2Fview%2Fstation%2FNE%3D51284622%2Freport', 
            { waitUntil: 'networkidle' }
        );

        // Login
        console.log('Logging in...');
        await page.getByRole('textbox', { name: 'Username or email' }).fill(process.env.FUSIONSOLAR_USERNAME);
        await page.getByRole('textbox', { name: 'Password' }).fill(process.env.FUSIONSOLAR_PASSWORD);
        await page.getByText('Log In').click();
        
        // Wait for navigation after login
        await page.waitForTimeout(3000);

        // Click the link to open plant list in new tab
        console.log('Opening plant list...');
        const page1Promise = page.waitForEvent('popup');
        await page.getByRole('link').nth(2).click();
        const page1 = await page1Promise;

        // Wait for plant list page to load
        await page1.waitForLoadState('networkidle');
        console.log('Searching for Nautica...');

        // Search for Nautica
        await page1.getByRole('textbox', { name: 'Plant name' }).click();
        await page1.getByRole('textbox', { name: 'Plant name' }).fill('Nautica');
        await page1.getByRole('button', { name: 'Search' }).click();
        await page1.waitForTimeout(2000);

        // Click on Nautica Shopping Centre
        console.log('Opening Nautica Shopping Centre...');
        await page1.getByRole('link', { name: 'Nautica Shopping Centre' }).click();
        await page1.waitForTimeout(2000);

        // Go to Report Management
        console.log('Opening Report Management...');
        await page1.getByText('Report Management').click();
        await page1.waitForTimeout(2000);

        // Export report
        console.log('Exporting report...');
        await page1.getByRole('button', { name: 'Export' }).click();
        await page1.waitForTimeout(2000);

        // Download the file
        console.log('Downloading file...');
        const downloadPromise = page1.waitForEvent('download');
        await page1.getByTitle('Download').click();
        const download = await downloadPromise;
        
        // Save the download
        const downloadPath = path.join(__dirname, 'data', 'nautica_raw.xlsx');
        await download.saveAs(downloadPath);
        console.log(`File downloaded to: ${downloadPath}`);

        // Close the export dialog
        await page1.getByRole('button', { name: 'Close' }).click();

        console.log('Download completed successfully!');

    } catch (error) {
        console.error('Error during download:', error);
        throw error;
    } finally {
        await browser.close();
    }
}

// Run the script
downloadNauticaData().catch(error => {
    console.error('Script failed:', error);
    process.exit(1);
});
