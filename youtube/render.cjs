// node render.cjs <dir>: frames of <dir>/page.html at 1920x1080, 24 fps, from <dir>/timeline.json.
const { chromium } = require('playwright');
const fs = require('fs');
const dir = process.argv[2], FPS = 24, tl = JSON.parse(fs.readFileSync(`${dir}/timeline.json`, 'utf8'));
(async () => {
  fs.rmSync(`${dir}/frames`, { recursive: true, force: true }); fs.mkdirSync(`${dir}/frames`);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', (e) => console.log('err', e.message));
  await p.goto(`http://127.0.0.1:8795/${dir}/page.html`); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(1500);
  await p.evaluate((x) => setTimeline(x), tl);
  const only = process.argv[3] ? process.argv[3].split(',').map(Number) : null;
  const n = Math.round(tl.total * FPS);
  for (let f = 0; f < n; f++) {
    const t = f / FPS - tl.lead;
    if (only && !only.some((s) => Math.abs(t - s) < 0.5 / FPS)) continue;
    await p.evaluate((x) => draw(x), Math.max(0, t));
    await p.screenshot({ path: `${dir}/frames/${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 88 });
  }
  console.log('frames', n); await b.close();
})();
