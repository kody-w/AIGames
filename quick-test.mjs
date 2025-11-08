import puppeteer from 'puppeteer';

async function testAvatarExplorer() {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    // Collect console messages
    const logs = {
        errors: [],
        warnings: [],
        info: [],
        all: []
    };

    page.on('console', msg => {
        const text = msg.text();
        const type = msg.type();
        logs.all.push({ type, text });

        if (type === 'error') logs.errors.push(text);
        if (type === 'warning') logs.warnings.push(text);
        if (type === 'log' || type === 'info') logs.info.push(text);
    });

    // Collect page errors
    page.on('pageerror', error => {
        logs.errors.push(`PAGE ERROR: ${error.toString()}`);
    });

    // Collect failed requests
    page.on('requestfailed', request => {
        logs.errors.push(`FAILED REQUEST: ${request.url()} - ${request.failure().errorText}`);
    });

    try {
        console.log('🧪 Testing avatar-3d-fps-explorer.html...\n');

        // Navigate to the page
        await page.goto('http://localhost:8080/avatar-3d-fps-explorer.html', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        // Wait for Three.js to initialize
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Check if canvas exists
        const hasCanvas = await page.evaluate(() => {
            return document.querySelector('canvas') !== null;
        });

        console.log('✓ Canvas element:', hasCanvas ? 'EXISTS' : 'MISSING');

        // Check if THREE is loaded (it's in module scope, check via window)
        const hasThree = await page.evaluate(() => {
            // Check if canvas and WebGL context exist as proof THREE.js is working
            const canvas = document.querySelector('canvas');
            if (!canvas) return false;
            const gl = canvas.getContext('webgl') || canvas.getContext('webgl2');
            return gl !== null;
        });

        console.log('✓ THREE.js/WebGL working:', hasThree ? 'YES' : 'NO');

        // Test button clicks
        console.log('\n📝 Testing UI buttons...');

        const toggleBtn = await page.$('#toggle-camera-btn');
        if (toggleBtn) {
            await toggleBtn.click();
            await new Promise(resolve => setTimeout(resolve, 500));
            console.log('✓ Toggle camera button: CLICKED');
        } else {
            console.log('✗ Toggle camera button: NOT FOUND');
        }

        const resetBtn = await page.$('#reset-position-btn');
        if (resetBtn) {
            await resetBtn.click();
            await new Promise(resolve => setTimeout(resolve, 500));
            console.log('✓ Reset position button: CLICKED');
        } else {
            console.log('✗ Reset position button: NOT FOUND');
        }

        // Check for specific errors
        const emissiveWarnings = logs.warnings.filter(w =>
            w.toLowerCase().includes('emissive')
        );

        const pointerLockErrors = logs.errors.filter(e =>
            e.toLowerCase().includes('pointer') &&
            e.toLowerCase().includes('null')
        );

        const controllerErrors = logs.errors.filter(e =>
            e.toLowerCase().includes('controller') &&
            e.toLowerCase().includes('not defined')
        );

        // Take screenshot
        await page.screenshot({ path: '/Users/kodyw/Library/CloudStorage/OneDrive-Microsoft/Projects/M365Agents/AIGames/test-screenshot.png', fullPage: false });
        console.log('\n📸 Screenshot saved: test-screenshot.png');

        // Print results
        console.log('\n' + '='.repeat(50));
        console.log('TEST RESULTS');
        console.log('='.repeat(50));

        console.log('\n🔍 Specific Error Checks:');
        console.log('  • Emissive warnings:', emissiveWarnings.length === 0 ? '✓ PASS (0)' : `✗ FAIL (${emissiveWarnings.length})`);
        console.log('  • Pointer lock null errors:', pointerLockErrors.length === 0 ? '✓ PASS (0)' : `✗ FAIL (${pointerLockErrors.length})`);
        console.log('  • Controller undefined errors:', controllerErrors.length === 0 ? '✓ PASS (0)' : `✗ FAIL (${controllerErrors.length})`);

        console.log('\n📊 Console Summary:');
        console.log(`  • Total errors: ${logs.errors.length}`);
        console.log(`  • Total warnings: ${logs.warnings.length}`);
        console.log(`  • Total info/log: ${logs.info.length}`);

        if (logs.errors.length > 0) {
            console.log('\n❌ ERRORS FOUND:');
            logs.errors.forEach((err, i) => {
                console.log(`  ${i + 1}. ${err}`);
            });
        }

        if (logs.warnings.length > 0) {
            console.log('\n⚠️  WARNINGS FOUND:');
            logs.warnings.forEach((warn, i) => {
                console.log(`  ${i + 1}. ${warn}`);
            });
        }

        if (logs.info.length > 0) {
            console.log('\n📝 INFO MESSAGES:');
            logs.info.forEach((info, i) => {
                console.log(`  ${i + 1}. ${info}`);
            });
        }

        // Final verdict
        const allPassed = hasCanvas &&
                         hasThree &&
                         emissiveWarnings.length === 0 &&
                         pointerLockErrors.length === 0 &&
                         controllerErrors.length === 0 &&
                         logs.errors.length === 0;

        console.log('\n' + '='.repeat(50));
        console.log('FINAL VERDICT:', allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED');
        console.log('='.repeat(50));

    } catch (error) {
        console.error('❌ Test execution failed:', error);
    } finally {
        await browser.close();
    }
}

testAvatarExplorer();
