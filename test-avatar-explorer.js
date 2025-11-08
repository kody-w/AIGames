const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({
        headless: false,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    // Collect console messages
    const consoleMessages = [];
    page.on('console', msg => {
        const text = msg.text();
        const type = msg.type();
        consoleMessages.push({ type, text });
        console.log(`[${type.toUpperCase()}] ${text}`);
    });

    // Collect page errors
    const pageErrors = [];
    page.on('pageerror', error => {
        pageErrors.push(error.toString());
        console.error('PAGE ERROR:', error);
    });

    try {
        // Navigate to the page
        await page.goto('http://localhost:8080/avatar-3d-fps-explorer.html', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        // Wait for Three.js to load
        await page.waitForTimeout(5000);

        // Check if scene loaded
        const sceneLoaded = await page.evaluate(() => {
            return typeof THREE !== 'undefined' && document.querySelector('canvas') !== null;
        });

        console.log('\n=== TEST RESULTS ===');
        console.log('Scene loaded:', sceneLoaded);

        // Test toggle camera button
        console.log('\nTesting Toggle Camera button...');
        await page.click('#toggle-camera-btn');
        await page.waitForTimeout(1000);

        // Test reset position button
        console.log('Testing Reset Position button...');
        await page.click('#reset-position-btn');
        await page.waitForTimeout(1000);

        // Check for specific errors
        const hasEmissiveWarnings = consoleMessages.some(m =>
            m.text.toLowerCase().includes('emissive') && m.type === 'warning'
        );

        const hasPointerLockErrors = consoleMessages.some(m =>
            m.text.toLowerCase().includes('pointer') &&
            m.text.toLowerCase().includes('null')
        );

        const hasControllerErrors = consoleMessages.some(m =>
            m.text.toLowerCase().includes('controller is not defined')
        );

        console.log('\n=== ERROR CHECK ===');
        console.log('Emissive warnings:', hasEmissiveWarnings);
        console.log('Pointer lock null errors:', hasPointerLockErrors);
        console.log('Controller undefined errors:', hasControllerErrors);
        console.log('Total console messages:', consoleMessages.length);
        console.log('Total page errors:', pageErrors.length);

        console.log('\n=== ALL CONSOLE MESSAGES ===');
        consoleMessages.forEach(m => {
            console.log(`[${m.type}] ${m.text}`);
        });

        if (pageErrors.length > 0) {
            console.log('\n=== PAGE ERRORS ===');
            pageErrors.forEach(err => console.log(err));
        }

        // Take screenshots
        await page.screenshot({ path: 'screenshot-explorer-initial.png', fullPage: true });
        console.log('\nScreenshot saved: screenshot-explorer-initial.png');

        // Test pointer lock by clicking canvas
        console.log('\nTesting pointer lock (clicking canvas)...');
        const canvas = await page.$('canvas');
        if (canvas) {
            await canvas.click();
            await page.waitForTimeout(2000);
            await page.screenshot({ path: 'screenshot-explorer-locked.png', fullPage: true });
            console.log('Screenshot saved: screenshot-explorer-locked.png');
        }

        console.log('\n=== FINAL STATUS ===');
        const allTestsPassed = !hasEmissiveWarnings &&
                               !hasPointerLockErrors &&
                               !hasControllerErrors &&
                               pageErrors.length === 0 &&
                               sceneLoaded;

        console.log('ALL TESTS PASSED:', allTestsPassed);

    } catch (error) {
        console.error('Test failed:', error);
    } finally {
        await browser.close();
    }
})();
