// Builds the queued reels for Instagram and Facebook.
// The backend queues a job (an id, the card images and how long each one shows); this script, run by the
// "Reels" GitHub Action, downloads the cards, animates them into a 1080x1920 video (the card's edges extended to fill the frame,
// slow zoom, slide between cards, optional music from music/) and uploads the MP4 to the backend,
// which publishes it. Nothing here needs a person: a job that fails is retried on the next run.
import { spawn } from 'node:child_process';
import { mkdtemp, writeFile, readFile, readdir, stat, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

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
async function makeReel(job, dir) {
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
    const theme = /^[\w.-]+\.mp3$/.test(job.music || '') ? join(THEMES_DIR.pathname, job.music) : null;
    await run(FF, fadeArgs(files, job.seconds, out, theme && await stat(theme).then(() => true, () => false) ? theme : await music()));
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
  await run(FF, reelArgs(files, secs, out, await music(), hook, bgs, !!job.endCard, narr));
  const size = (await stat(out)).size;
  if (size < 100000) throw new Error(`video too small (${size} bytes)`);
  return out;
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
      const out = await makeReel(job, dir);
      const up = await fetch(`${API}/v2/reels/upload?id=${encodeURIComponent(job.id)}&key=${encodeURIComponent(KEY)}`, {
        method: 'POST', headers: { 'Content-Type': 'video/mp4' }, body: await readFile(out), signal: AbortSignal.timeout(120000) });
      console.log(`${job.id}: uploaded ${(await stat(out)).size} bytes -> ${up.status}`);
    } catch (e) {
      console.log(`${job.id}: failed: ${e.message}`);
      await fetch(`${API}/v2/reels/upload?id=${encodeURIComponent(job.id)}&key=${encodeURIComponent(KEY)}&failed=1`, { method: 'POST', body: String(e.message).slice(0, 300) }).catch(() => {});
    } finally { await rm(dir, { recursive: true, force: true }); }
  }
}
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) main().catch((e) => { console.error(e); process.exit(1); });
