const puppeteer = require('puppeteer');
(async () => {
    try {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
        page.on('pageerror', error => console.log('BROWSER EXCEPTION:', error.message));
        await page.goto('http://localhost:3000/result/ds-ebeef7df7cf0', { waitUntil: 'networkidle2' });
        await new Promise(resolve => setTimeout(resolve, 2000));
        await browser.close();
    } catch (e) {
        console.error(e);
    }
})();
