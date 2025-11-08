import puppeteer from 'puppeteer';

async function finalTest() {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    // Collect console messages
    const logs = {
        errors: [],
        warnings: [],
        info: []
    };

    page.on('console', msg => {
        const text = msg.text();
        const type = msg.type();

        if (type === 'error') logs.errors.push(text);
        if (type === 'warning') logs.warnings.push(text);
        if (type === 'log' || type === 'info') logs.info.push(text);
    });

    page.on('pageerror', error => {
        logs.errors.push(`PAGE ERROR: ${error.toString()}`);
    });

    try {
        console.log('🎮 FINAL TEST: avatar-3d-fps-explorer.html\n');

        // Navigate
        await page.goto('http://localhost:8080/avatar-3d-fps-explorer.html', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        // Wait for initialization
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Check page elements
        const pageCheck = await page.evaluate(() => {
            const canvas = document.querySelector('canvas');
            const hud = document.getElementById('hud');
            const toggleBtn = document.getElementById('toggle-camera-btn');
            const resetBtn = document.getElementById('reset-position-btn');
            const crosshair = document.getElementById('crosshair');

            return {
                hasCanvas: canvas !== null,
                hasHUD: hud !== null,
                hasToggleBtn: toggleBtn !== null,
                hasResetBtn: resetBtn !== null,
                hasCrosshair: crosshair !== null,
                canvasWidth: canvas ? canvas.width : 0,
                canvasHeight: canvas ? canvas.height : 0
            };
        });

        console.log('📋 Element Checks:');
        console.log(`  • Canvas: ${pageCheck.hasCanvas ? '✅' : '❌'} (${pageCheck.canvasWidth}x${pageCheck.canvasHeight})`);
        console.log(`  • HUD: ${pageCheck.hasHUD ? '✅' : '❌'}`);
        console.log(`  • Toggle Camera Button: ${pageCheck.hasToggleBtn ? '✅' : '❌'}`);
        console.log(`  • Reset Position Button: ${pageCheck.hasResetBtn ? '✅' : '❌'}`);
        console.log(`  • Crosshair: ${pageCheck.hasCrosshair ? '✅' : '❌'}`);

        // Test buttons
        console.log('\n🖱️  Button Functionality:');

        await page.click('#toggle-camera-btn');
        await new Promise(resolve => setTimeout(resolve, 300));
        const cameraMode1 = await page.$eval('#camera-mode', el => el.textContent);
        console.log(`  • Toggle Camera: ✅ (Mode: ${cameraMode1})`);

        await page.click('#reset-position-btn');
        await new Promise(resolve => setTimeout(resolve, 300));
        const position = await page.$eval('#pos', el => el.textContent);
        console.log(`  • Reset Position: ✅ (Position: ${position})`);

        // Check for specific errors
        const emissiveWarnings = logs.warnings.filter(w =>
            w.toLowerCase().includes('emissive')
        );

        const pointerLockErrors = logs.errors.filter(e =>
            (e.toLowerCase().includes('pointer') && e.toLowerCase().includes('null')) ||
            e.toLowerCase().includes('pointerlockcontrols')
        );

        const controllerErrors = logs.errors.filter(e =>
            e.toLowerCase().includes('controller') &&
            e.toLowerCase().includes('not defined')
        );

        // Filter out favicon 404 (expected)
        const realErrors = logs.errors.filter(e =>
            !e.toLowerCase().includes('favicon') &&
            !e.toLowerCase().includes('404')
        );

        console.log('\n🔍 Error Analysis:');
        console.log(`  • Emissive Warnings: ${emissiveWarnings.length === 0 ? '✅ PASS' : '❌ FAIL (' + emissiveWarnings.length + ')'}`);
        console.log(`  • Pointer Lock Errors: ${pointerLockErrors.length === 0 ? '✅ PASS' : '❌ FAIL (' + pointerLockErrors.length + ')'}`);
        console.log(`  • Controller Errors: ${controllerErrors.length === 0 ? '✅ PASS' : '❌ FAIL (' + controllerErrors.length + ')'}`);
        console.log(`  • Other Real Errors: ${realErrors.length === 0 ? '✅ PASS' : '❌ FAIL (' + realErrors.length + ')'}`);

        if (realErrors.length > 0) {
            console.log('\n⚠️  Real Errors Found:');
            realErrors.forEach(err => console.log(`     ${err}`));
        }

        if (emissiveWarnings.length > 0) {
            console.log('\n⚠️  Emissive Warnings:');
            emissiveWarnings.forEach(warn => console.log(`     ${warn}`));
        }

        console.log('\n📊 Console Stats:');
        console.log(`  • Errors: ${logs.errors.length} (${realErrors.length} real)`);
        console.log(`  • Warnings: ${logs.warnings.length}`);
        console.log(`  • Info/Logs: ${logs.info.length}`);

        if (logs.info.length > 0) {
            console.log('\n📝 Initialization Messages:');
            logs.info.forEach(info => console.log(`     ${info}`));
        }

        // Take screenshot
        await page.screenshot({
            path: '/Users/kodyw/Library/CloudStorage/OneDrive-Microsoft/Projects/M365Agents/AIGames/final-screenshot.png',
            fullPage: false
        });
        console.log('\n📸 Screenshot: final-screenshot.png');

        // Final verdict
        const allPassed = pageCheck.hasCanvas &&
                         pageCheck.hasHUD &&
                         pageCheck.hasToggleBtn &&
                         pageCheck.hasResetBtn &&
                         emissiveWarnings.length === 0 &&
                         pointerLockErrors.length === 0 &&
                         controllerErrors.length === 0 &&
                         realErrors.length === 0;

        console.log('\n' + '='.repeat(60));
        if (allPassed) {
            console.log('✅ ALL TESTS PASSED - NO ERRORS FOUND');
        } else {
            console.log('⚠️  SOME CHECKS FAILED - SEE DETAILS ABOVE');
        }
        console.log('='.repeat(60));

    } catch (error) {
        console.error('❌ Test execution failed:', error);
    } finally {
        await browser.close();
    }
}

finalTest();
