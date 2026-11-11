// Builds the queued reels for Instagram and Facebook.
// The backend queues a job (an id, the card images and how long each one shows); this script, run by the
// "Reels" GitHub Action, downloads the cards, animates them into a 1080x1920 video (the card's edges extended to fill the frame,
// slow zoom, slide between cards, optional music from music/) and uploads the MP4 to the backend,
// which publishes it. Nothing here needs a person: a job that fails is retried on the next run.
import { spawn } from 'node:child_process';
import { mkdtemp, writeFile, readFile, readdir, stat, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
// The runner's own Chrome when the workflow found one (PW_CHROME): no browser download or system libraries to install,
// minutes saved before a live reel (owner, 2026-11-05: «السيرفر هو اللي ما يتأخرش في صنع الفيديو»); else Playwright's.
async function launchBrowser(chromium) {
  if (process.env.PW_CHROME) {
    try { return await chromium.launch({ executablePath: process.env.PW_CHROME }); } catch (e) {
      console.log('system Chrome failed, installing Playwright\'s:', String(e.message || e).slice(0, 160));
      const { execSync } = await import('node:child_process');
      try { execSync('npx playwright install --with-deps chromium', { stdio: 'inherit', timeout: 300000 }); } catch (e2) { console.log('playwright install failed'); }
      delete process.env.PW_CHROME;
    }
  }
  return chromium.launch();
}

const API = process.env.REELS_API || 'https://api.football-legend.com';
const KEY = process.env.REELS_KEY || '';
const FF = process.env.FFMPEG || 'ffmpeg';
const MUSIC_DIR = new URL('./music/', import.meta.url);
const THEMES_DIR = new URL('./themes/', import.meta.url); // a series' own track, never picked at random for other reels
const FPS = 30, W = 1080, H = 1920, CARD_H = 1350, FADE = 0.5;

function run(cmd, args) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { stdio: ['ignore', 'ignore', 'pipe'] });
    let err = '';
    p.stderr.on('data', (d) => { err = (err + d).slice(-4000); });
    p.on('close', (code, signal) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exited ${code ?? signal}: ${err.split('\n').filter((l) => !/deprecated pixel format|Last message repeated/.test(l)).join('\n').slice(-600)}`))));
  });
}
async function music() {
  try {
    const files = (await readdir(MUSIC_DIR)).filter((f) => /\.(mp3|m4a|aac|wav)$/i.test(f));
    return files.length ? join(MUSIC_DIR.pathname, files[Math.floor(Math.random() * files.length)]) : null;
  } catch { return null; }
}
// The reel's track (owner, 2026-11-10: «موسيقه الفيديو مختلفة»): the one the server handed it (job.music: its own from
// themes/, or the next of music/ in turn), else a random one of music/.
async function trackFor(job) {
  if (/^[\w.-]+\.mp3$/.test(job.music || '')) {
    for (const d of [THEMES_DIR, MUSIC_DIR]) { const f = join(d.pathname, job.music); if (await stat(f).then(() => true, () => false)) return f; }
  }
  return music();
}
const BAND = (H - CARD_H) / 2;
// The still 1080x1920 background of one card: its own top and bottom edges stretched to fill the frame above and
// below it, so the video reads as one tall card. A blurred copy of the card there looked like a letterbox: Meta flags
// that as "your video has a border" (repurposed content) and limits the reel's reach. It is made by its own ffmpeg
// run: built inside the reel's filter graph (split, vstack, loop), ffmpeg 6.1 aborted with "corrupted double-linked
// list" whenever the hook was laid over it, and every reel with a hook failed (2026-10-06).
export function backgroundArgs(card, out) {
  return ['-y', '-i', card, '-filter_complex',
    `[0:v]scale=${W}:${CARD_H},split=3[t][m][u];[t]crop=${W}:4:0:0,scale=${W}:${BAND}[tt];[u]crop=${W}:4:0:${CARD_H - 4},scale=${W}:${BAND}[uu];[tt][m][uu]vstack=inputs=3`,
    '-frames:v', '1', '-q:v', '2', out];
}
// ffmpeg arguments for cards shown `secs[i]` seconds each over their backgrounds `bgs[i]` (backgroundArgs), joined by a
// slide. `hook` (optional) is a transparent 1080x1920 PNG laid over the whole video: a title above the card and a
// question under it.
export function reelArgs(frames, secs, out, track, hook, bgs, endCard = false, narr = null) {
  const args = ['-y'];
  frames.forEach((f) => args.push('-i', f));
  if (track) args.push('-stream_loop', '-1', '-i', track);
  else args.push('-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo');
  if (hook) args.push('-loop', '1', '-framerate', String(FPS), '-i', hook);
  const bg0 = frames.length + 1 + (hook ? 1 : 0);
  bgs.forEach((b, i) => args.push('-loop', '1', '-framerate', String(FPS), '-t', String(secs[i]), '-i', b));
  if (narr) args.push('-i', narr);
  const parts = [];
  frames.forEach((_, i) => {
    const n = Math.round(secs[i] * FPS);
    parts.push(`[${i}:v]scale=${W}:${CARD_H},zoompan=z='min(zoom+0.0006,1.07)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${n}:s=${W}x${CARD_H}:fps=${FPS}[ff${i}]`);
    parts.push(`[${bg0 + i}:v][ff${i}]overlay=0:${BAND}:shortest=1,fps=${FPS},format=yuv420p,setsar=1,settb=AVTB[v${i}]`);
  });
  let last = 'v0', offset = 0;
  for (let i = 1; i < frames.length; i++) {
    offset += secs[i - 1] - FADE;
    parts.push(`[${last}][v${i}]xfade=transition=slideleft:duration=${FADE}:offset=${offset.toFixed(2)}[x${i}]`);
    last = `x${i}`;
  }
  const total = secs.reduce((a, b) => a + b, 0) - FADE * (frames.length - 1);
  const a = frames.length;
  if (hook) {
    // Shown from the first frame: the first second has to say what the reel is about. With an end card (the "تابعنا"
    // card the backend adds last), it goes when the slide to that card starts.
    const until = endCard && frames.length > 1 ? `:enable='lt(t,${(secs.slice(0, -1).reduce((x, y) => x + y, 0) - FADE * (frames.length - 1)).toFixed(2)})'` : '';
    parts.push(`[${a + 1}:v]format=rgba[hk]`, `[${last}][hk]overlay=0:0:shortest=1:format=auto${until},format=yuv420p[vh]`);
    last = 'vh';
  }
  // With a narration (YouTube tests, owner 2026-10-28) the music goes under the voice.
  if (narr) {
    parts.push(`[${a}:a]atrim=0:${total.toFixed(2)},volume=0.16,afade=t=in:d=0.5,afade=t=out:st=${Math.max(0, total - 1.2).toFixed(2)}:d=1.2[mus]`,
      `[${bg0 + bgs.length}:a]aresample=44100,apad,atrim=0:${total.toFixed(2)}[nar]`, '[nar][mus]amix=inputs=2:duration=first:normalize=0[aout]');
  } else parts.push(`[${a}:a]atrim=0:${total.toFixed(2)},afade=t=in:d=0.5,afade=t=out:st=${Math.max(0, total - 1.2).toFixed(2)}:d=1.2[aout]`);
  args.push('-filter_complex', parts.join(';'), '-map', `[${last}]`, '-map', '[aout]',
    '-t', total.toFixed(2), '-r', String(FPS), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-maxrate', '2400k', '-bufsize', '4800k', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out);
  return args;
}
// The coach series (job.mode 'fade'): full 1080x1920 frames that share their photo, joined by a plain cross-fade with no
// zoom or slide, so only the panel under the photo changes. Its own track (job.music, from themes/).
export function fadeArgs(frames, secs, out, track) {
  const args = ['-y'];
  frames.forEach((f, i) => args.push('-loop', '1', '-framerate', String(FPS), '-t', String(secs[i]), '-i', f));
  if (track) args.push('-stream_loop', '-1', '-i', track);
  else args.push('-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo');
  const parts = frames.map((_, i) => `[${i}:v]scale=${W}:${H},fps=${FPS},format=yuv420p,setsar=1,settb=AVTB[v${i}]`);
  let last = 'v0', offset = 0;
  for (let i = 1; i < frames.length; i++) {
    offset += secs[i - 1] - FADE;
    parts.push(`[${last}][v${i}]xfade=transition=fade:duration=${FADE}:offset=${offset.toFixed(2)}[x${i}]`);
    last = `x${i}`;
  }
  const total = secs.reduce((a, b) => a + b, 0) - FADE * (frames.length - 1);
  parts.push(`[${frames.length}:a]atrim=0:${total.toFixed(2)},afade=t=in:d=0.3,afade=t=out:st=${Math.max(0, total - 1.5).toFixed(2)}:d=1.5[aout]`);
  args.push('-filter_complex', parts.join(';'), '-map', `[${last}]`, '-map', '[aout]',
    '-t', total.toFixed(2), '-r', String(FPS), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-maxrate', '2400k', '-bufsize', '4800k', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out);
  return args;
}
// Width and height from a JPEG's SOF marker.
function jpegSize(b) {
  for (let i = 2; i + 9 < b.length;) {
    if (b[i] !== 0xff) return null;
    const m = b[i + 1], len = b.readUInt16BE(i + 2);
    if (m >= 0xc0 && m <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(m)) return { w: b.readUInt16BE(i + 7), h: b.readUInt16BE(i + 5) };
    i += 2 + len;
  }
  return null;
}
// The narration (job.voice: one line per card, the YouTube tests of owner 2026-10-28): each line read by the site's
// voice (/v2/reels/voice, Gemini), each card held long enough for its line, the lines laid where their cards start.
// Any line that cannot be read drops the whole narration: the reel then goes out with music only, as before.
function probeSeconds(f) {
  return new Promise((resolve) => {
    const p = spawn(process.env.FFPROBE || 'ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], { stdio: ['ignore', 'pipe', 'ignore'] });
    let o = ''; p.stdout.on('data', (d) => { o += d; }); p.on('close', () => resolve(Number(o) || 0));
  });
}
async function narration(job, dir, secs) {
  if (!Array.isArray(job.voice) || !job.voice.some(Boolean)) return null;
  const clips = [];
  for (let i = 0; i < secs.length; i++) {
    const text = String(job.voice[i] || '').trim();
    if (!text) { clips.push(null); continue; }
    const u = `${API}/v2/reels/voice?key=${encodeURIComponent(KEY)}&voice=${encodeURIComponent(job.voiceName || 'Puck')}&text=${encodeURIComponent(text)}`;
    let buf = null;
    for (let t = 0; t < 3 && !buf; t++) {
      const res = await fetch(u, { signal: AbortSignal.timeout(120000) }).catch(() => null);
      const b = res?.ok ? Buffer.from(await res.arrayBuffer()) : null;
      if (b && b.length > 2000 && b.toString('latin1', 0, 4) === 'RIFF') buf = b;
      else await new Promise((r) => setTimeout(r, 8000));
    }
    if (!buf) { console.log(`${job.id}: narration line ${i + 1} failed, music only`); return null; }
    const f = join(dir, `v${i}.wav`);
    await writeFile(f, buf);
    const d = await probeSeconds(f);
    secs[i] = Math.max(secs[i], d + 1.1);
    clips.push(f);
  }
  const inputs = [], parts = [];
  let start = 0;
  clips.forEach((f, i) => {
    if (f) { const k = inputs.length / 2; inputs.push('-i', f); parts.push(`[${k}:a]aresample=44100,adelay=${Math.round((start + 0.35) * 1000)}:all=1[c${k}]`); }
    start += secs[i] - FADE;
  });
  const n = inputs.length / 2;
  const out = join(dir, 'narration.wav');
  await run(FF, ['-y', ...inputs, '-filter_complex', `${parts.join(';')};${Array.from({ length: n }, (_, k) => `[c${k}]`).join('')}amix=inputs=${n}:duration=longest:normalize=0[o]`, '-map', '[o]', out]);
  return out;
}
// A narrated story (job.voiceLines, one line a beat: «TONIGHT'S RESULTS» told match by match, owner 2026-11-03): each
// line read, trimmed and timed; each beat lasts its line plus a breath (at least its own minimum, d.minBeats), the page
// gets the beats (d.beats: [start, length]) and the lines are laid at their starts. Any line that fails: no voice, the
// beats keep their minimums.
async function voiceBeats(job, d, dir) {
  const lines = Array.isArray(job.voiceLines) ? job.voiceLines : null, mins = d.minBeats || [];
  if (!lines || !lines.length) return null;
  const files = [];
  for (let i = 0; i < lines.length; i++) {
    const one = await animVoice({ ...job, voiceText: lines[i] }, dir, 60, `line${i}`).catch((e) => { console.log(`${job.id}: line ${i + 1} (${e.message})`); return null; });
    if (!one) { console.log(`${job.id}: line ${i + 1} of ${lines.length} could not be read, no narration`); files.length = 0; break; }
    files.push(one);
    // the voice answers 502 when called too fast; a long narration can ask for more room (job.voiceGap, seconds: Gemini's
    // per-minute share ran out on the eight lines of the Ronaldo farewell, 2026-11-05)
    await new Promise((r) => setTimeout(r, Math.max(2.5, Number(job.voiceGap) || 0) * 1000));
  }
  let t = 0;
  const beats = mins.map((m, i) => { const len = Math.max(m, files[i] ? files[i].d + 0.55 : 0); const b = [t, len]; t += len; return b; });
  d.beats = beats;
  if (!files.length) return null;
  // Each line's time in the video, told to the server for Facebook's closed captions (owner, 2026-11-10)
  job.cues = files.map((f, i) => [beats[i][0] + 0.25, beats[i][0] + 0.25 + f.d]);
  const out = join(dir, 'story.wav'), parts = [], inputs = [];
  files.forEach((f, i) => { inputs.push('-i', f.path); parts.push(`[${i}:a]aresample=44100,adelay=${Math.round((beats[i][0] + 0.25) * 1000)}:all=1[c${i}]`); });
  await run(FF, ['-y', ...inputs, '-filter_complex', `${parts.join(';')};${files.map((_, i) => `[c${i}]`).join('')}amix=inputs=${files.length}:duration=longest:normalize=0[o]`, '-map', '[o]', out]);
  return out;
}
// One spoken line for a moving reel (job.voiceText, read by the site's voice: Gemini, its voice, style and accent),
// three tries; it must end before the reel does.
async function animVoice(job, dir, total, name = '') {
  const text = String(job.voiceText || '').trim();
  if (!text) return null;
  const q = new URLSearchParams({ key: KEY, text, voice: job.voiceName || 'Fenrir', ...(job.voiceStyle ? { style: job.voiceStyle } : {}), ...(job.voiceLang ? { lang: job.voiceLang } : {}) });
  // A long narration (job.voiceGap) waits out Gemini's share instead of giving up (2026-11-06: the Ronaldo farewell went out
  // with its first line only): six tries, 45 s apart, each failure logged.
  const tries = job.voiceGap ? 6 : 3, wait = job.voiceGap ? 45000 : 20000;
  for (let t = 0; t < tries; t++) {
    const res = await fetch(`${API}/v2/reels/voice?${q}`, { signal: AbortSignal.timeout(120000) }).catch(() => null);
    if (!res?.ok) console.log(`${job.id}: voice ${name || 'line'} try ${t + 1}: ${res ? res.status + ' ' + (await res.clone().text().catch(() => '')).slice(0, 90) : 'no answer'}`);
    const b = res?.ok ? Buffer.from(await res.arrayBuffer()) : null;
    if (b && b.length > 2000 && b.toString('latin1', 0, 4) === 'RIFF') {
      const raw = join(dir, `${name || 'said'}-raw.wav`), f = join(dir, `${name || 'said'}.wav`);
      await writeFile(raw, b);
      // Silence trimmed at both ends; a line far longer than its words (the style read out with it, 2026-11-03) is not used.
      await run(FF, ['-y', '-i', raw, '-af', 'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse', f]);
      // A pause written in the line («Messi... four.») is read as one: each is given time (2026-11-10: the verdict's round
      // two, 15 words in 11.3 s, was taken for the style read out); a line still too long is read again, not given up at once.
      const d = await probeSeconds(f), words = text.split(/\s+/).length, pauses = (text.match(/\.\.\.|…/g) || []).length;
      if (d > words * 0.6 + 1.5 + pauses * 0.9) { console.log(`${job.id}: voice ${name || 'line'} try ${t + 1}: ${d.toFixed(1)} s for ${words} words, read again`); await new Promise((r) => setTimeout(r, 8000)); continue; }
      if (d > 0.5 && d < total - 0.6) return name ? { path: f, d } : f;
      throw new Error(`line of ${d.toFixed(1)} s for a ${total} s reel`);
    }
    await new Promise((r) => setTimeout(r, wait)); // the voice answers 502 when called too fast
  }
  return null;
}
// Moving reels (owner, 2026-11-03: «الريلز القديم بدائي»): each kind drawn in its own page (anim/<kind>.html: the league
// table, the day's matches, before the match, the line-up, full time, a star in numbers) from job.anim, recorded frame
// by frame (window.draw(t), window.TOTAL). Any failure falls back to the still cards (job.frames).
async function makeAnim(job, dir) {
  const { chromium } = await import('playwright');
  const d = JSON.parse(JSON.stringify(job.anim));
  // Every picture the page needs (crests, a star's photo) is fetched here and put in as data: the page loads nothing.
  const pics = [];
  const walk = (o) => { if (!o || typeof o !== 'object') return; for (const [k, v] of Object.entries(o)) { if (typeof v === 'string' && /^(logo|homeLogo|awayLogo|photo)$/.test(k) && /^https?:/.test(v)) pics.push([o, k]); else walk(v); } };
  walk(d);
  const cache = new Map();
  for (const [o, k] of pics) {
    if (!cache.has(o[k])) {
      try {
        // Wikimedia refuses requests without a User-Agent (2026-11-03: the star's photo was missing on a runner).
        const res = await fetch(o[k], { headers: { 'User-Agent': 'FootballLegendsReels/1.0 (https://football-legend.com)' }, signal: AbortSignal.timeout(20000) });
        const buf = Buffer.from(await res.arrayBuffer());
        cache.set(o[k], res.ok && buf.length > 200 ? `data:${res.headers.get('content-type') || 'image/png'};base64,${buf.toString('base64')}` : '');
      } catch { cache.set(o[k], ''); }
    }
    o[k] = cache.get(o[k]);
  }
  const story = await voiceBeats(job, d, dir).catch((e) => { console.log(`${job.id}: story voice skipped (${e.message})`); return null; });
  const page0 = await readFile(new URL(`./anim/${d.kind}.html`, import.meta.url), 'utf8');
  const html = new URL(`./anim/_${job.id.replace(/[^\w-]/g, '_')}.html`, import.meta.url);
  await writeFile(html, page0.replace('</head>', `<script>window.DATA=${JSON.stringify(d).replace(/</g, '\\u003c')};</script></head>`));
  const frames = join(dir, 'af');
  await run('mkdir', ['-p', frames]);
  const b = await launchBrowser(chromium);
  try {
    const p = await b.newPage({ viewport: { width: W, height: H } });
    const errs = []; p.on('pageerror', (e) => errs.push(e.message));
    await p.goto(html.href);
    await p.evaluate(() => document.fonts.ready);
    await p.evaluate(() => Promise.all([...document.images].map((i) => (i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; })))));
    await p.waitForTimeout(500);
    if (errs.length) throw new Error('page: ' + errs[0]);
    const total = await p.evaluate(() => window.TOTAL), fps = 30;
    // The first frame is the finished card (window.POSTER): Instagram's grid, Facebook and Telegram show a reel by its
    // first frame, and the animation starts on an empty background (owner, 2026-11-03: «ليه الريلز الجديد كله طالع بخلفية سودا»).
    const poster = await p.evaluate(() => (typeof window.POSTER === 'number' ? window.POSTER : null));
    for (let i = 0; i < Math.round(total * fps); i++) {
      await p.evaluate((t) => window.draw(t), i === 0 && poster != null ? poster : i / fps);
      await p.screenshot({ path: join(frames, `${String(i).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 90 });
    }
    // the cover: the page at its cover moment, the progress bar and the teaser hidden
    try {
      const ct = await p.evaluate(() => (typeof window.COVER === 'number' ? window.COVER : typeof window.POSTER === 'number' ? window.POSTER : window.TOTAL * 0.6));
      await p.evaluate((t) => { window.draw(t); document.querySelectorAll('body > div').forEach((el) => { if (/z-index: ?9[89]/.test(el.getAttribute('style') || '')) el.style.display = 'none'; }); }, ct);
      await p.screenshot({ path: join(dir, 'cover.jpg'), type: 'jpeg', quality: 90 });
      job.coverPath = join(dir, 'cover.jpg');
    } catch (e) { console.log(`${job.id}: cover skipped (${e.message})`); }
    const out = join(dir, 'reel.mp4');
    // A spoken line over the start (FB Legends, owner 2026-11-03: «صوت حماسي رايق يليق بالأوروبيين», voice Fenrir):
    // the music goes under it; a line that cannot be read leaves the reel with music only.
    // A narrated reel that must be told whole (job.voiceGap) is not made with its first line alone: it fails and is tried
    // again on a later run, when the voice's share is back.
    if (!story && job.voiceGap && Array.isArray(job.voiceLines)) throw new Error('the narration could not be read whole');
    const said = story || await animVoice(job, dir, total).catch((e) => { console.log(`${job.id}: voice skipped (${e.message})`); return null; });
    // job.duck (owner, 2026-11-06: «الصوت و المزيكا ... لايقين على بعض»): the music dips under each spoken line and comes
    // back up in the pauses (a sidechain compressor keyed by the voice), so it can sit louder without covering the words.
    // job.voiceClean (owner, 2026-11-05: «في وش في الصوت»): the voice's hiss taken out (a noise filter, then nothing above
    // 7.5 kHz) before it is laid over the music.
    // A reel's own track (job.music from themes/, e.g. the farewell piano; owner 2026-11-05: «موسيقى غير المعتادة») and
    // its level under the voice (job.musicVol), else a random one of music/ at 0.2.
    if (said && !story) job.cues = [[0.3, 0.3 + await probeSeconds(said)]]; // the one line's time, for the captions
    if (!said) delete job.cues;
    job.voiced = !!said; // told to the server: a reel without its voice carries no AI label (owner, 2026-11-10)
    let track = await trackFor(job);
    const mv = Number(job.musicVol) > 0 ? Number(job.musicVol) : 0.2;
    // A reel longer than its track (2026-11-10: the Manchester reel, 83 s over a 54 s track, went silent for a second where the
    // track faded out and started again): the track joined to itself with a crossfade, so the music never stops.
    const td = await probeSeconds(track);
    if (td > 5 && total > td - 3) {
      const long = join(dir, 'music-long.wav');
      await run(FF, ['-y', '-i', track, '-i', track, '-i', track, '-filter_complex', '[0:a][1:a]acrossfade=d=4[x];[x][2:a]acrossfade=d=4[o]', '-map', '[o]', long]);
      track = long;
    }
    console.log(`${job.id}: music ${job.music || track.split('/').pop()}${said ? `, voice${job.duck ? ' ducked' : ''}${job.voiceClean ? ' cleaned' : ''}` : ', no voice'}`);
    const mix = said
      ? `[1:a]volume=${mv},afade=t=in:d=0.5,afade=t=out:st=${total - 1.5}:d=1.5[m];[2:a]aresample=44100,${job.voiceClean ? 'afftdn=nf=-28,lowpass=f=7500,' : ''}adelay=${story ? 0 : 300}:all=1,apad[v];${job.duck ? '[v]asplit=2[v1][v2];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=700[md];[md][v2]' : '[m][v]'}amix=inputs=2:duration=first:normalize=0[a]`
      : `[1:a]volume=0.5,afade=t=in:d=0.5,afade=t=out:st=${total - 1.5}:d=1.5[a]`;
    await run(FF, ['-y', '-framerate', String(fps), '-i', join(frames, '%05d.jpg'), '-stream_loop', '-1', '-i', track, ...(said ? ['-i', said] : []),
      '-filter_complex', mix, '-map', '0:v', '-map', '[a]',
      '-c:v', 'libx264', '-crf', '22', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-t', String(total), '-movflags', '+faststart', out]);
    if ((await stat(out)).size < 100000) throw new Error('video too small');
    // The server takes up to 24 MB (2026-11-10: the Manchester reel, two grounds from the air over 80 s, came to 40 MB and
    // was refused): a bigger one is made again at the bitrate that fits, the sound kept as it is.
    const MAXB = 22 * 1024 * 1024, size = (await stat(out)).size;
    if (size > MAXB) {
      const kb = Math.max(600, Math.floor((MAXB * 8) / 1024 / total * 0.92) - 140), small = join(dir, 'reel-fit.mp4');
      await run(FF, ['-y', '-i', out, '-c:v', 'libx264', '-b:v', `${kb}k`, '-maxrate', `${kb}k`, '-bufsize', `${kb * 2}k`, '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', small]);
      console.log(`${job.id}: ${(size / 1048576).toFixed(1)} MB, made again at ${kb} kb/s: ${((await stat(small)).size / 1048576).toFixed(1)} MB`);
      return small;
    }
    return out;
  } finally { await b.close(); await rm(html, { force: true }); }
}
// The reel's cover (owner, 2026-11-10: «صورة مصغرة تكون متماشية مع تصميم كل فيديو ... في ريل عبارة عن جداول و في ريلز
// عبارة عن مقارنة بين لاعبين»): the reel's own page at its cover moment (window.COVER, else its POSTER: the finished
// table, both players face to face, the hook's headline), without the progress bar and the teaser; a reel of still
// cards: its first card on the reel's own background. job.coverPath.
async function stillCover(job, dir) {
  if (!job.frames?.length) return null;
  const res = await fetch(job.frames[0], { signal: AbortSignal.timeout(60000) }), card = join(dir, 'cover-card.png'), out = join(dir, 'cover.jpg');
  if (!res.ok) return null;
  await writeFile(card, Buffer.from(await res.arrayBuffer()));
  await run(FF, backgroundArgs(card, join(dir, 'cover-full.png')));
  await run(FF, ['-y', '-i', join(dir, 'cover-full.png'), '-q:v', '3', out]);
  return out;
}
// A cover alone for a reel already posted (owner, 2026-11-10: the English page's older reels): its page drawn at its
// cover moment, its pictures put in as data like makeAnim does, no frames recorded and no voice asked.
async function coverOnly(job, dir) {
  if (!job.anim) return stillCover(job, dir);
  const { chromium } = await import('playwright');
  const d = JSON.parse(JSON.stringify(job.anim)), pics = [];
  const walk = (o) => { if (!o || typeof o !== 'object') return; for (const [k, v] of Object.entries(o)) { if (typeof v === 'string' && /^(logo|homeLogo|awayLogo|photo|hl|al)$/.test(k) && /^https?:/.test(v)) pics.push([o, k]); else walk(v); } };
  walk(d);
  const cache = new Map();
  for (const [o, k] of pics) {
    if (!cache.has(o[k])) { try { const res = await fetch(o[k], { headers: { 'User-Agent': 'FootballLegendsReels/1.0 (https://football-legend.com)' }, signal: AbortSignal.timeout(20000) }); const buf = Buffer.from(await res.arrayBuffer()); cache.set(o[k], res.ok && buf.length > 200 ? `data:${res.headers.get('content-type') || 'image/png'};base64,${buf.toString('base64')}` : ''); } catch { cache.set(o[k], ''); } }
    o[k] = cache.get(o[k]);
  }
  const page0 = await readFile(new URL(`./anim/${d.kind}.html`, import.meta.url), 'utf8');
  const html = new URL(`./anim/_cv_${job.id.replace(/[^\w-]/g, '_')}.html`, import.meta.url);
  await writeFile(html, page0.replace('</head>', `<script>window.DATA=${JSON.stringify(d).replace(/</g, '\\u003c')};</script></head>`));
  const b = await launchBrowser(chromium);
  try {
    const p = await b.newPage({ viewport: { width: W, height: H } });
    await p.goto(html.href);
    await p.evaluate(() => document.fonts.ready);
    await p.evaluate(() => Promise.all([...document.images].map((i) => (i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; })))));
    await p.waitForTimeout(500);
    const ct = await p.evaluate(() => (typeof window.COVER === 'number' ? window.COVER : typeof window.POSTER === 'number' ? window.POSTER : window.TOTAL * 0.6));
    await p.evaluate((t) => { window.draw(t); document.querySelectorAll('body > div').forEach((el) => { if (/z-index: ?9[89]/.test(el.getAttribute('style') || '')) el.style.display = 'none'; }); }, ct);
    const out = join(dir, 'cover.jpg');
    await p.screenshot({ path: out, type: 'jpeg', quality: 90 });
    return out;
  } finally { await b.close(); await rm(html, { force: true }); }
}
async function makeReel(job, dir) {
  // Any kind with its page in anim/ is drawn by it (2026-11-04: «en-rate» had its page but was missing from a hand-kept
  // list, so it went to the still cards with none and ffmpeg failed three times).
  const kind = String(job.anim?.kind || '');
  // A kind may carry a digit (2026-11-11: «en-top5» did not pass a letters-only test, went to the still cards with none
  // and ffmpeg failed three times).
  if (/^[a-z][a-z0-9-]*$/.test(kind) && await stat(new URL(`./anim/${kind}.html`, import.meta.url)).then(() => true, () => false)) {
    try { return await makeAnim(job, dir); } catch (e) { console.log(`${job.id}: moving ${job.anim.kind} failed (${e.message}), the still cards instead`); }
  }
  // A video made elsewhere (the app ad, owner 2026-10-24): taken as it is, only checked to be an MP4.
  if (job.video) {
    const res = await fetch(job.video, { signal: AbortSignal.timeout(120000) });
    const buf = Buffer.from(await res.arrayBuffer());
    if (!res.ok || buf.length < 100000 || buf.toString('latin1', 4, 8) !== 'ftyp') throw new Error(`video not an MP4 (${res.status}, ${buf.length} bytes)`);
    const out = join(dir, 'reel.mp4');
    await writeFile(out, buf);
    return out;
  }
  const files = [];
  for (let i = 0; i < job.frames.length; i++) {
    const res = await fetch(job.frames[i], { signal: AbortSignal.timeout(60000) });
    const buf = Buffer.from(await res.arrayBuffer());
    if (!res.ok || buf.length < 15000 || buf[0] !== 0xff || buf[1] !== 0xd8) {
      const why = buf.length < 400 ? `: ${buf.toString('utf8').replace(/\s+/g, ' ').slice(0, 160)}` : '';
      throw new Error(`frame ${i} not a JPEG (${res.status}, ${buf.length} bytes)${why}`);
    }
    const size = jpegSize(buf);
    const fh = job.mode === 'fade' ? H : CARD_H;
    if (!size || size.w !== 1080 || size.h !== fh) throw new Error(`frame ${i} is ${size ? size.w + 'x' + size.h : 'unreadable'}, not 1080x${fh}`);
    const f = join(dir, `f${i}.jpg`);
    await writeFile(f, buf);
    files.push(f);
  }
  if (job.mode === 'fade') {
    const out = join(dir, 'reel.mp4');
    await run(FF, fadeArgs(files, job.seconds, out, await trackFor(job)));
    if ((await stat(out)).size < 100000) throw new Error('video too small');
    return out;
  }
  // The hook is optional: a reel without it is still worth posting.
  let hook = null;
  if (job.hook) {
    try {
      const res = await fetch(job.hook, { signal: AbortSignal.timeout(60000) });
      const buf = Buffer.from(await res.arrayBuffer());
      if (res.ok && buf.length > 500 && buf.readUInt32BE(0) === 0x89504e47 && buf.readUInt32BE(16) === W && buf.readUInt32BE(20) === H) {
        hook = join(dir, 'hook.png');
        await writeFile(hook, buf);
      } else console.log(`${job.id}: hook skipped (${res.status}, ${buf.length} bytes)`);
    } catch (e) { console.log(`${job.id}: hook skipped (${e.message})`); }
  }
  const bgs = [];
  for (let i = 0; i < files.length; i++) {
    const bg = join(dir, `bg${i}.jpg`);
    await run(FF, backgroundArgs(files[i], bg));
    bgs.push(bg);
  }
  const out = join(dir, 'reel.mp4'), secs = [...job.seconds];
  const narr = await narration(job, dir, secs).catch((e) => { console.log(`${job.id}: narration skipped (${e.message})`); return null; });
  if (!narr) secs.splice(0, secs.length, ...job.seconds);
  if (Array.isArray(job.voice) && job.voice.some(Boolean)) job.voiced = !!narr;
  await run(FF, reelArgs(files, secs, out, await trackFor(job), hook, bgs, !!job.endCard, narr));
  const size = (await stat(out)).size;
  if (size < 100000) throw new Error(`video too small (${size} bytes)`);
  return out;
}
// A photo post (FB Legends, owner 2026-11-04: «ممكن نضيف صور بردة»): the page at 1080x1350, taken once as a JPEG.
export async function makeImage(job, dir) {
  const d = job.anim || {};
  const page0 = await readFile(new URL(`./anim/${d.kind}.html`, import.meta.url), 'utf8');
  const html = new URL(`./anim/_${job.id.replace(/[^\w-]/g, '_')}.html`, import.meta.url);
  await writeFile(html, page0.replace('</head>', `<script>window.DATA=${JSON.stringify(d).replace(/</g, '\\u003c')};</script></head>`));
  const { chromium } = await import('playwright');
  const b = await launchBrowser(chromium);
  try {
    const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
    const errs = []; p.on('pageerror', (e) => errs.push(e.message));
    await p.goto(html.href);
    await p.evaluate(() => document.fonts.ready);
    await p.evaluate(() => Promise.all([...document.images].map((i) => (i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; })))));
    await p.waitForTimeout(500);
    if (errs.length) throw new Error('page: ' + errs[0]);
    await p.evaluate(() => window.draw && window.draw(typeof window.POSTER === 'number' ? window.POSTER : 0));
    const out = join(dir, 'post.jpg');
    await p.screenshot({ path: out, type: 'jpeg', quality: 92 });
    return out;
  } finally { await b.close(); await rm(html, { force: true }); }
}
async function main() {
  if (!KEY) { console.log('No REELS_KEY: nothing to do.'); return; }
  const res = await fetch(`${API}/v2/reels/jobs?key=${encodeURIComponent(KEY)}`, { signal: AbortSignal.timeout(30000) });
  if (!res.ok) throw new Error(`jobs ${res.status}`);
  const { jobs = [] } = await res.json();
  console.log(`${jobs.length} reel job(s)`);
  for (const job of jobs) {
    const dir = await mkdtemp(join(tmpdir(), 'reel-'));
    try {
      const out = job.image ? await makeImage(job, dir) : await makeReel(job, dir);
      const up = await fetch(`${API}/v2/reels/upload?id=${encodeURIComponent(job.id)}&key=${encodeURIComponent(KEY)}${typeof job.voiced === 'boolean' ? `&voiced=${job.voiced ? 1 : 0}` : ''}${Array.isArray(job.cues) && job.cues.length ? `&cues=${job.cues.map(([x, y]) => `${x.toFixed(2)}-${y.toFixed(2)}`).join(',')}` : ''}`, {
        method: 'POST', headers: { 'Content-Type': job.image ? 'image/jpeg' : 'video/mp4' }, body: await readFile(out), signal: AbortSignal.timeout(120000) });
      console.log(`${job.id}: uploaded ${(await stat(out)).size} bytes -> ${up.status}`);
      // a refused upload counts as a failed try (2026-11-10: a 40 MB reel was refused and made again every run, its voice each time)
      if (!up.ok) throw new Error(`upload refused: ${up.status} ${(await up.text().catch(() => '')).slice(0, 120)}`);
      // its cover, after the video (a cover that fails leaves the reel as it is)
      if (!job.image) {
        try {
          const cv = job.coverPath || await stillCover(job, dir);
          if (!cv) throw new Error('none for this kind');
          const cu = await fetch(`${API}/v2/reels/upload?id=${encodeURIComponent(job.id)}&key=${encodeURIComponent(KEY)}&cover=1`, { method: 'POST', headers: { 'Content-Type': 'image/jpeg' }, body: await readFile(cv), signal: AbortSignal.timeout(60000) });
          console.log(`${job.id}: cover -> ${cu.status}`);
        } catch (e) { console.log(`${job.id}: cover skipped (${e.message})`); }
      }
    } catch (e) {
      console.log(`${job.id}: failed: ${e.message}`);
      await fetch(`${API}/v2/reels/upload?id=${encodeURIComponent(job.id)}&key=${encodeURIComponent(KEY)}&failed=1`, { method: 'POST', body: String(e.message).slice(0, 300) }).catch(() => {});
    } finally { await rm(dir, { recursive: true, force: true }); }
  }
}
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) main().catch((e) => { console.error(e); process.exit(1); });
export { makeAnim, coverOnly };
