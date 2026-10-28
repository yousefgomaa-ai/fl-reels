const { chromium } = require('playwright');
const fs = require('fs');
// One narration read in a single call; each line starts where whisper heard its first words.
const FPS = 30, LEAD = 0.5;
const lines = fs.readFileSync('caps.txt', 'utf8').trim().split('\n').filter(Boolean);
const W = JSON.parse(fs.readFileSync('voice.json', 'utf8'));
const WORDS = W.flatMap((s) => s.w || []);
const TM = JSON.parse(fs.readFileSync('timing.json', 'utf8'));
const STARTS = TM.starts;
const END = TM.end;
const seg = [], caps = [];
lines.forEach((l, i) => {
  const a = STARTS[i], b = i + 1 < STARTS.length ? STARTS[i + 1] : END;
  // the line's last word (whisper's segments can span several lines)
  const ws = WORDS.filter((w) => w[0] >= a - 0.01 && w[0] < b - 0.01);
  const segEnd = ws.length ? Math.min(b, ws[ws.length - 1][0] + 0.5) : b;
  seg.push([a + LEAD, segEnd + LEAD]);
  const bounds = W.filter((s) => s.s > a + 0.01 && s.s < b - 0.01).map((s) => s.s).concat(WORDS.filter((w, k) => k && w[0] > a + 0.01 && w[0] < b - 0.01 && w[0] - WORDS[k - 1][0] > 0.55).map((w) => w[0]));
  const parts = l.split(/(?<=[،.:؟!])\s+/), tot = parts.reduce((x, p) => x + p.length, 0);
  let c = a, acc = 0;
  parts.forEach((p, k) => {
    acc += p.length;
    let e = k === parts.length - 1 ? b : a + (segEnd - a) * acc / tot;
    if (k < parts.length - 1 && bounds.length) e = bounds.reduce((x, y) => (Math.abs(y - e) < Math.abs(x - e) ? y : x));
    caps.push([c + LEAD, e + LEAD, p]); c = e;
  });
});
const total = END + LEAD + 1.5;
fs.writeFileSync('timeline.json', JSON.stringify({ seg, caps, total }));
(async () => {
  fs.rmSync('frames', { recursive: true, force: true }); fs.mkdirSync('frames');
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', (e) => console.log('err', e.message));
  await p.goto(`http://127.0.0.1:8794/${process.env.DIR}/page.html`); await p.evaluate(() => document.fonts.ready);
  await p.evaluate((tl) => setTimeline(tl), { seg, caps });
  const n = Math.round(total * FPS);
  for (let f = 0; f < n; f++) { await p.evaluate((x) => draw(x), f / FPS); await p.screenshot({ path: `frames/${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 90 }); }
  console.log('frames', n, 'seconds', total.toFixed(1)); await b.close();
})();
