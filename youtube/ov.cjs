// node ov.cjs [dir...]: lists any element wider than the 1920 px frame, scene by scene (owner, 2026-10-30).
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const dir of process.argv.length > 2 ? process.argv.slice(2) : ['round', 'preview', 'history']) {
    const tl = JSON.parse(fs.readFileSync(`${dir}/timeline.json`, 'utf8'));
    await p.goto(`http://127.0.0.1:8795/${dir}/page.html`); await p.evaluate(() => document.fonts.ready); await p.evaluate((x) => setTimeline(x), tl);
    for (let i = 0; i < tl.starts.length; i++) {
      await p.evaluate((x) => draw(x), tl.starts[i] + 2.4);
      const r = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, sx: window.scrollX, wide: [...document.querySelectorAll('.scene')].filter((s) => s.style.visibility === 'visible').flatMap((s) => [...s.querySelectorAll('*')]).filter((e) => { const q = e.getBoundingClientRect(); return q.left < -1 || q.right > 1921; }).slice(0, 3).map((e) => e.className + ':' + Math.round(e.getBoundingClientRect().left) + '..' + Math.round(e.getBoundingClientRect().right)) }));
      if (r.sw > 1920 || r.sx || r.wide.length) console.log(dir, i, JSON.stringify(r));
    }
  }
  await b.close(); console.log('checked');
})();
