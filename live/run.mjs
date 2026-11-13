// FB Legends live results stream (owner, 2026-11-13): opens the page's live video, shows live/scoreboard.html in a real
// browser on a virtual screen, streams the screen and a quiet track to Facebook, refreshes the scores every 20 s from the
// site's own live list and ends the live once the day's games are over (or at the time limit). The stream address comes
// from the API with the reels key and is never printed.
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
const API = 'https://api.football-legend.com', KEY = process.env.REELS_KEY, SLUG = process.env.LIVE_SLUG || 'uefa.nations';
const PUBLISH = process.env.LIVE_PUBLISH === '1', MAXMIN = Number(process.env.LIVE_MAX_MIN || 150), TITLE = process.env.LIVE_TITLE || 'UEFA Nations League LIVE scores';
const DESC = process.env.LIVE_DESC || 'Live scores from every UEFA Nations League game tonight, updated every 30 seconds. Predict the final scores in the comments and follow FB Legends for every result.';
const ymd = (t) => new Date(t).toISOString().slice(0, 10).replace(/-/g, '');
async function games() {
  const r = await fetch(`${API}/matches?date=${ymd(Date.now())}`, { signal: AbortSignal.timeout(20000) });
  const d = await r.json();
  return (d.events || []).filter((e) => e.leagueSlug === SLUG && !/israel/i.test(`${e.teams?.home?.name} ${e.teams?.away?.name}`));
}
async function api(q) {
  const r = await fetch(`${API}/v2/fben/live?key=${encodeURIComponent(KEY)}&${new URLSearchParams(q)}`, { signal: AbortSignal.timeout(30000) });
  const d = await r.json(); if (!r.ok || d.error) throw new Error(`live api: ${d.error || r.status}`); return d;
}
const lv = await api({ do: 'start', title: TITLE, desc: DESC, ...(PUBLISH ? { publish: '1' } : {}) });
if (!lv.stream) throw new Error('no stream address');
console.log(`live video ${lv.id} (${PUBLISH ? 'published' : 'unpublished test'}) ${lv.link || ''}`);
const b = await chromium.launch({ headless: false, executablePath: process.env.PW_CHROME || undefined,
  args: ['--kiosk', '--window-position=0,0', '--window-size=720,1280', '--no-first-run', '--disable-infobars', '--autoplay-policy=no-user-gesture-required'] });
const p = await b.newPage({ viewport: { width: 720, height: 1280 } });
await p.goto(new URL('./scoreboard.html', import.meta.url).href);
const push = async () => { try { const g = await games(); await p.evaluate(([g, t]) => window.update(g, t), [g, 'UEFA NATIONS LEAGUE']); return g; } catch (e) { console.log('scores: ' + e.message); return null; } };
await push();
const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'warning', '-f', 'x11grab', '-video_size', '720x1280', '-framerate', '30', '-draw_mouse', '0', '-i', process.env.DISPLAY || ':99',
  '-stream_loop', '-1', '-i', new URL('../music/fl-warmup.mp3', import.meta.url).pathname,
  '-filter_complex', '[1:a]volume=0.25[a]', '-map', '0:v', '-map', '[a]',
  '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency', '-b:v', '2500k', '-maxrate', '2500k', '-bufsize', '5000k', '-pix_fmt', 'yuv420p', '-g', '60', '-keyint_min', '60',
  '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-f', 'flv', lv.stream], { stdio: ['ignore', 'inherit', 'inherit'] });
let ended = false; ff.on('exit', (c) => { console.log('ffmpeg exited ' + c); ended = true; });
const t0 = Date.now(); let doneAt = 0;
while (!ended && Date.now() - t0 < MAXMIN * 60000) {
  await new Promise((r) => setTimeout(r, 20000));
  const g = await push();
  if (g && g.length && g.every((e) => e.fixture?.status?.state === 'post')) { doneAt ||= Date.now(); if (Date.now() - doneAt > 12 * 60000) break; } else doneAt = 0;
  if (g && !g.length && Date.now() - t0 > 10 * 60000) break;
}
console.log('ending the live');
ff.kill('SIGINT'); await new Promise((r) => setTimeout(r, 5000));
await api({ do: 'end', id: lv.id }).then(() => console.log('live ended'), (e) => console.log(e.message));
await b.close();
