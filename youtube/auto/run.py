# python3 youtube/auto/run.py: makes the oldest waiting long YouTube video of football-legend.com (owner, 2026-10-30).
# The site's API gives the job (its data only); the script is written here from templates, read in one voice call,
# checked number by number against whisper, drawn at 1920x1080 and kept as a GitHub Release asset. The site is then
# told, and it asks the owner on Telegram (👁 watch, 🚀 YouTube). A number read wrong holds the video.
import json, os, re, shutil, subprocess, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); YT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build import round_video, preview_video
from check import align, numbers_check, captions, chapters, stamp, LEAD
from arnum import numbers_in

API = 'https://api.football-legend.com'
KEY = os.environ.get('REELS_KEY', '')
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0; football-legend.com)'}
STYLE = 'Read aloud in a warm, natural Egyptian Arabic accent, like an Egyptian football presenter on TV:'
DIR = os.path.join(YT, 'job')
MUSIC = os.path.join(YT, '..', 'music', 'fl-golden.mp3')
BLANK = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='


CUR = {}


def api(path, body=None):
    q = '&' if '?' in path else '?'
    req = urllib.request.Request(f'{API}{path}{q}key={urllib.parse.quote(KEY, safe="")}', data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Content-Type': 'application/json', **UA})
    return json.loads(urllib.request.urlopen(req, timeout=60).read() or b'{}')


def report(job, **kw):
    if len(sys.argv) > 1:
        return print('report', json.dumps(kw, ensure_ascii=False)[:3000])
    for t in range(4):
        try:
            return api('/v2/ytv/done', {'id': job['id'], **kw})
        except Exception as e:
            print('report try', t + 1, e); time.sleep(10 * (t + 1))


def logos(job):
    urls = []
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ('logo', 'homeLogo', 'awayLogo') and isinstance(v, str) and v.startswith('https://'): urls.append(v)
                else: walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(job)
    os.makedirs(f'{DIR}/logo', exist_ok=True)
    got = {}
    for i, u in enumerate(dict.fromkeys(urls)):
        try:
            data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
            open(f'{DIR}/logo/{i:02d}.png', 'wb').write(data); got[u] = f'logo/{i:02d}.png'
        except Exception as e:
            print('logo failed', u, e)
    return lambda u: got.get(u, BLANK)


def colour(path):
    """A club's colour from its crest: the most common strong colour, darkened enough for white cards and text."""
    import colorsys
    from PIL import Image
    try:
        im = Image.open(path).convert('RGBA').resize((64, 64))
    except Exception:
        return None
    buckets = {}
    for r, g, b, a in im.getdata():
        if a < 200 or max(r, g, b) - min(r, g, b) < 40 or max(r, g, b) < 40: continue
        k = (r // 32, g // 32, b // 32)
        s = buckets.setdefault(k, [0, 0, 0, 0]); s[0] += r; s[1] += g; s[2] += b; s[3] += 1
    if not buckets: return None
    r, g, b, n = max(buckets.values(), key=lambda s: s[3])
    return colorsys.rgb_to_hls(r / n / 255, g / n / 255, b / n / 255)


def shades(hls, fallback):
    import colorsys
    h, l, s = hls or fallback
    hexc = lambda l2: '#%02x%02x%02x' % tuple(round(c * 255) for c in colorsys.hls_to_rgb(h, max(0.08, min(l2, 0.9)), s))
    base = min(l, 0.42)
    return hexc(base), hexc(base * 0.55), hexc(min(base * 1.25, 0.5))


def voice(text):
    body = json.dumps({'text': text}).encode()
    q = f'{API}/v2/reels/voice?key={urllib.parse.quote(KEY, safe="")}&voice=Puck&lang=ar-EG&style={urllib.parse.quote(STYLE, safe="")}'
    for t in range(4):
        try:
            open('/tmp/v.wav', 'wb').write(urllib.request.urlopen(urllib.request.Request(q, data=body, headers={'Content-Type': 'application/json', **UA}), timeout=300).read())
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', '/tmp/v.wav', '-b:a', '160k', f'{DIR}/voice.mp3'], check=True)
            return True
        except Exception as e:
            print('voice try', t + 1, e, (e.read()[:300] if hasattr(e, 'read') else b''))
            time.sleep(60 * (t + 1))  # the voice endpoint answers 502 when called too fast
    return False


def pcm(path, a=None, b=None):
    import numpy as np
    cut = (['-ss', str(max(0, a))] if a is not None else []) + (['-to', str(b)] if b is not None else [])
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', *cut, '-i', path, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def main():
    # A job file (a test run on a branch) is made without asking the site or telling it.
    jobs = [json.load(open(sys.argv[1]))] if len(sys.argv) > 1 else api('/v2/ytv/jobs').get('jobs') or []
    if not jobs:
        print('no long videos waiting'); return
    job = jobs[0]
    CUR.update(id=job['id'])
    print('job', job['id'], job['kind'])
    report(job, state='making')
    shutil.rmtree(DIR, ignore_errors=True); os.makedirs(DIR)
    L = logos(job)
    if job['kind'] == 'round':
        made, why = round_video(job, L)
    else:
        hc = colour(os.path.join(DIR, L(job['home']['logo']))) if not L(job['home']['logo']).startswith('data:') else None
        ac = colour(os.path.join(DIR, L(job['away']['logo']))) if not L(job['away']['logo']).startswith('data:') else None
        made, why = preview_video(job, L, (shades(hc, (0.98, 0.3, 0.8)), shades(ac, (0.6, 0.3, 0.6))))
    if not made:
        print('held:', why); return report(job, state='held', reason=why)
    S, html, meta = made
    open(f'{DIR}/page.html', 'w').write(html)
    lines = [l['text'] for l in S.lines]
    open(f'{DIR}/voice.txt', 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    if not voice('\n\n'.join(lines)):
        return report(job, state='failed', reason='voice')
    from faster_whisper import WhisperModel
    m = WhisperModel('small', device='cpu', compute_type='int8')
    segs, _ = m.transcribe(pcm(f'{DIR}/voice.mp3'), language='ar', word_timestamps=True)
    words = [[round(w.start, 2), round(w.end, 2), w.word.strip()] for s in segs for w in (s.words or [])]
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f'{DIR}/voice.mp3'], capture_output=True, text=True).stdout.strip())
    starts, cover, at, owner = align(lines, words, dur)
    for i, l in enumerate(lines): print(f'{starts[i]:7.2f} {cover[i]:.2f} {l[:70]}')
    bad = numbers_check(lines, [l['nums'] for l in S.lines], words, starts, dur)
    if bad:
        # A doubtful number is heard again by the bigger model before anything is held (the career videos' rule).
        big = WhisperModel('large-v3', device='cpu', compute_type='int8')
        for i in list(bad):
            a, b = starts[i] - 1.0, (starts[i + 1] if i + 1 < len(starts) else dur) + 1.0
            heard = ' '.join(s.text for s in big.transcribe(pcm(f'{DIR}/voice.mp3', a, b), language='ar')[0])
            left = [n for n in bad[i] if n not in numbers_in(heard)]
            print('large-v3', i, bad[i], '->', left, '|', heard)
            if left: bad[i] = {'missing': left, 'heard': heard.strip()[:200]}
            else: del bad[i]
    lost = [i for i, c in enumerate(cover) if c < 0.3]
    if bad or lost:
        why = '; '.join([f'السطر {i + 1}: الرقم {x["missing"]} مش مسموع (اتسمع: {x["heard"]})' for i, x in bad.items()] + [f'السطر {i + 1} مش مقروء تقريبًا' for i in lost])
        print('held:', why)
        return report(job, state='held', reason=why[:1500], lines=[lines[i] for i in list(bad)[:5]])
    caps = captions(lines, starts, dur, words, at, owner)
    tl = {'starts': [round(s, 2) for s in starts], 'end': round(dur, 2), 'lead': LEAD, 'total': round(dur + LEAD + 1.5, 2), 'caps': caps}
    json.dump(tl, open(f'{DIR}/timeline.json', 'w'), ensure_ascii=False)
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8795', '-d', YT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        ov = subprocess.run(['node', 'ov.cjs', 'job'], cwd=YT, capture_output=True, text=True)
        print(ov.stdout, ov.stderr)
        if ov.returncode or 'checked' not in ov.stdout or len(ov.stdout.strip().splitlines()) > 1:
            return report(job, state='held', reason='عنصر أعرض من الإطار: ' + ov.stdout.strip()[:600])
        subprocess.run(['bash', 'make.sh', 'job', MUSIC], cwd=YT, check=True)
    finally:
        srv.kill()
    out = f'{YT}/out-job.mp4'
    secs = round(float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out], capture_output=True, text=True).stdout.strip()))
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', out, '-vf', 'scale=854:-2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', f'{YT}/prev.mp4'], check=True)
    if os.path.getsize(f'{YT}/prev.mp4') > 19 * 1024 * 1024:
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', out, '-vf', 'scale=640:-2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '34', '-c:a', 'aac', '-b:a', '48k', '-movflags', '+faststart', f'{YT}/prev.mp4'], check=True)
    # Kept as a release of this repository, not in git: 14 videos a week of 20-60 MB would bloat it.
    tag = job['id']
    vid, prev = f'{tag}.mp4', f'{tag}-preview.mp4'
    shutil.copy(out, f'/tmp/{vid}'); shutil.copy(f'{YT}/prev.mp4', f'/tmp/{prev}')
    subprocess.run(['gh', 'release', 'delete', tag, '--yes', '--cleanup-tag'], capture_output=True)
    subprocess.run(['gh', 'release', 'create', tag, f'/tmp/{vid}', f'/tmp/{prev}', '--title', meta['title'][:120], '--notes', '\n'.join(lines)], check=True)
    repo = os.environ.get('GITHUB_REPOSITORY', 'yousefgomaa-ai/fl-reels')
    base = f'https://github.com/{repo}/releases/download/{tag}'
    ch = chapters(lines, [l['chap'] for l in S.lines], starts)
    desc = meta['about'] + ('\n\n' + '\n'.join(f'{stamp(t)} {c}' for t, c in ch) if ch else '')
    report(job, state='ready', video=f'{base}/{vid}', preview=f'{base}/{prev}', size=os.path.getsize(out), seconds=secs,
           title=meta['title'][:100], description=desc, tags=meta['tags'], script=lines)
    print('ready', base, secs, 's', os.path.getsize(out), 'bytes')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback; traceback.print_exc()
        if CUR.get('id'): report(CUR, state='failed', reason=str(e)[:300])
        sys.exit(1)
