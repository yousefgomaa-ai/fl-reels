const { chromium } = require('playwright');
const [dir, n, out] = [process.argv[2], Number(process.argv[3]), process.argv[4]];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', (e) => console.log('err', e.message));
  await p.goto(`http://127.0.0.1:8794/${dir}/page.html`); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(800);
  const seg = Array.from({ length: n }, (_, i) => [i * 8 + 0.5, i * 8 + 8.5]);
  await p.evaluate((t) => setTimeline(t), { seg, caps: [] });
  const shots = [];
  for (let i = 0; i < n; i++) { await p.evaluate((x) => draw(x), i === 0 ? 1.5 : seg[i][0] + 3); await p.screenshot({ path: `${dir}/pv${i}.png` }); shots.push(`${dir}/pv${i}.png`); }
  console.log(shots.join(' ')); await b.close();
})();
