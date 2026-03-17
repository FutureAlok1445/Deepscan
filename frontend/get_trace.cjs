const puppeteer = require('puppeteer');
(async () => {
    try {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        
        page.on('pageerror', error => {
            console.log('--- REACT CRASH STACK TRACE ---');
            console.log(error.stack || error.message);
        });
        
        await page.goto('http://localhost:3000/result/ds-ebeef7df7cf0', { waitUntil: 'networkidle2' });
        await new Promise(resolve => setTimeout(resolve, 3000));
        await browser.close();
    } catch (e) { }
})();
