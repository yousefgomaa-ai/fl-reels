// node still.cjs <dir>: one still per scene, 2.4 s into it, to check by eye.
const { chromium } = require('playwright'); const fs = require('fs');
const dir = process.argv[2], tl = JSON.parse(fs.readFileSync(`${dir}/timeline.json`, 'utf8'));
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', (e) => console.log('err', e.message)); p.on('console', (m) => m.type() === 'error' && console.log('console', m.text()));
  await p.goto(`http://127.0.0.1:8795/${dir}/page.html`); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(1500);
  await p.evaluate((x) => setTimeline(x), tl);
  for (let i = 0; i < tl.starts.length; i++) { await p.evaluate((x) => draw(x), tl.starts[i] + 2.4); await p.screenshot({ path: `${dir}/st${String(i).padStart(2, '0')}.jpg`, type: 'jpeg', quality: 70 }); }
  await b.close(); console.log('ok');
})();
