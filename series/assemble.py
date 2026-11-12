# Builds an episode from series/ep<N>.json and the Kaggle shots in series/ep<N>/shots (owner, 2026-11-12).
# Each character keeps one voice for the whole series (the json's "cast"); the score is synthesised per scene mood,
# from tones only (no noise beds: the hiss the owner heard, 2026-11-11), ducked under the voices.
import json, os, subprocess, sys, time
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from PIL import Image, ImageDraw, ImageFilter, ImageFont

EPN = int(sys.argv[1]) if len(sys.argv) > 1 else 1
D = os.path.dirname(os.path.abspath(__file__))
EP = json.load(open(os.path.join(D, f'ep{EPN}.json')))
SHOTS_DIR = os.path.join(D, f'ep{EPN}', 'shots')
B = os.path.join(D, f'ep{EPN}', 'build')
os.makedirs(B, exist_ok=True)
W, H, FPS, SR = 1080, 1920, 30, 44100
CLIP = 81 / 16
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
COLORS = {'narrator': (255, 255, 255), 'emma': (255, 224, 138), 'mark': (159, 211, 255), 'operator': (220, 220, 220)}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:])
        raise SystemExit(f'failed: {" ".join(cmd[:6])}')
    return r.stdout


def dur(f):
    return float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).strip())


def load_audio(f):
    raw = run_bytes(['ffmpeg', '-v', 'error', '-i', f, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'])
    return np.frombuffer(raw, dtype=np.float32).copy()


def run_bytes(cmd):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        print(r.stderr[-2000:]); raise SystemExit('ffmpeg decode failed')
    return r.stdout


# ---------- voices (one per character, never swapped: a failure stops the build) ----------
def tts(who, text, out):
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        return
    voice = EP['cast'][who]
    rate = {'narrator': '-8%', 'emma': '-4%', 'mark': '-6%'}.get(who, '+0%')
    for t in range(8):
        r = subprocess.run(['edge-tts', '--voice', voice, f'--rate={rate}', '--text', text, '--write-media', out], capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 2000:
            return
        print('tts retry', who, t, r.stderr[-160:])
        time.sleep(5 + 5 * t)
    raise SystemExit(f'no voice for {who}: the build stops rather than change the voice')


# ---------- timeline ----------
LEAD, GAP, TAIL = 0.3, 0.25, 0.5
plan, t = [], 0.0
for s in EP['shots']:
    lines = []
    for k, (who, text) in enumerate(s.get('lines', [])):
        f = os.path.join(B, f"{s['id']}_{k}.mp3")
        tts(who, text, f)
        lines.append({'who': who, 'text': text, 'file': f, 'len': dur(f)})
    need = LEAD + sum(l['len'] for l in lines) + GAP * max(len(lines) - 1, 0) + TAIL if lines else 0
    default = 4.0 if (s.get('v') or s.get('reuse')) else 3.0
    d = max(s.get('dur', 0) or 0, need, 1.2 if s.get('dur') else default)
    lt = LEAD
    for l in lines:
        l['at'] = lt; lt += l['len'] + GAP
    plan.append({'s': s, 'start': t, 'dur': round(d, 2), 'lines': lines})
    t += round(d, 2)
TOTAL = t
print('total', round(TOTAL, 1), 's,', len(plan), 'shots')


# ---------- stills ----------
def cover(im):
    im = im.convert('RGB')
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def frame_of(sid, at=2.5):
    p = os.path.join(B, f'bg_{sid}.jpg')
    if not os.path.exists(p):
        run(['ffmpeg', '-v', 'error', '-y', '-ss', str(at), '-i', os.path.join(SHOTS_DIR, sid + '.mp4'), '-frames:v', '1', p])
    return Image.open(p)


def dark_bg(src):
    if src is None:
        return Image.new('RGB', (W, H), (8, 9, 12))
    im = cover(src).filter(ImageFilter.GaussianBlur(16))
    return Image.blend(im, Image.new('RGB', (W, H), (0, 0, 0)), 0.55)


def phone(ph, src, call=None):
    im = dark_bg(src); d = ImageDraw.Draw(im)
    px, py, pw, phh = 150, 300, 780, 1280
    d.rounded_rectangle((px - 18, py - 18, px + pw + 18, py + phh + 18), 90, fill=(22, 22, 25))
    d.rounded_rectangle((px, py, px + pw, py + phh), 72, fill=(10, 10, 12))
    ft, fn, fm = ImageFont.truetype(BOLD, 34), ImageFont.truetype(BOLD, 46), ImageFont.truetype(REG, 42)
    name = call or ph['from']
    d.text((px + pw / 2, py + 60), (ph or {}).get('time', '3:08 AM'), font=ft, fill=(200, 200, 205), anchor='mm')
    d.ellipse((px + pw / 2 - 60, py + 110, px + pw / 2 + 60, py + 230), fill=(88, 88, 96))
    d.text((px + pw / 2, py + 170), name[0], font=fn, fill='white', anchor='mm')
    d.text((px + pw / 2, py + 280), name, font=fn, fill='white', anchor='mm')
    if call:
        d.text((px + pw / 2, py + 350), 'calling...', font=ImageFont.truetype(REG, 38), fill=(170, 170, 175), anchor='mm')
        d.ellipse((px + pw / 2 - 70, py + phh - 230, px + pw / 2 + 70, py + phh - 90), fill=(235, 50, 50))
        d.text((px + pw / 2, py + phh - 160), 'END', font=ImageFont.truetype(BOLD, 36), fill='white', anchor='mm')
        return im
    d.line((px + 40, py + 335, px + pw - 40, py + 335), fill=(45, 45, 50), width=2)
    y = py + 380
    for side, text in ph['msgs']:
        words, rows, cur = text.split(), [], ''
        for w_ in words:
            if d.textlength((cur + ' ' + w_).strip(), font=fm) > pw - 200:
                rows.append(cur); cur = w_
            else:
                cur = (cur + ' ' + w_).strip()
        rows.append(cur)
        bw = max(d.textlength(r, font=fm) for r in rows) + 60
        bh = 52 * len(rows) + 40
        x0, col = (px + 40, (58, 58, 62)) if side == 'in' else (px + pw - 40 - bw, (10, 132, 255))
        if text == 'RUN.':
            col = (200, 20, 30)
        d.rounded_rectangle((x0, y, x0 + bw, y + bh), 40, fill=col)
        for k, r in enumerate(rows):
            d.text((x0 + 30, y + 20 + 52 * k + 26), r, font=fm, fill='white', anchor='lm')
        y += bh + 28
    return im


def laptop(names, src):
    im = dark_bg(src); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 90, 560, 990, 1140
    d.rounded_rectangle((x0 - 20, y0 - 20, x1 + 20, y1 + 20), 24, fill=(30, 30, 34))
    d.rectangle((x0, y0, x1, y1), fill=(18, 32, 52))
    d.polygon([(x0 - 80, y1 + 20), (x1 + 80, y1 + 20), (x1 + 140, y1 + 90), (x0 - 140, y1 + 90)], fill=(40, 40, 46))
    f = ImageFont.truetype(BOLD, 30)
    for k, n in enumerate(names):
        cx, cy = x0 + 130 + (k % 4) * 210, y0 + 200
        hot = n == 'MARK'
        d.rectangle((cx - 60, cy - 40, cx + 60, cy + 40), fill=(230, 180, 60) if not hot else (210, 40, 40))
        d.rectangle((cx - 60, cy - 55, cx - 10, cy - 40), fill=(230, 180, 60) if not hot else (210, 40, 40))
        d.text((cx, cy + 75), n, font=f, fill='white', anchor='mm')
        if hot:
            d.rectangle((cx - 85, cy - 80, cx + 85, cy + 110), outline=(255, 70, 70), width=5)
    return im


def title(text):
    im = Image.new('RGB', (W, H), (4, 4, 6)); d = ImageDraw.Draw(im)
    f, f2 = ImageFont.truetype(SERIF, 120), ImageFont.truetype(BOLD, 42)
    for k, row in enumerate(text.split(' ', 1) if len(text) > 9 else [text]):
        d.text((W / 2, 860 + k * 150), row, font=f, fill=(225, 25, 35), anchor='mm')
    d.text((W / 2, 1180), f"EPISODE {EP['episode']}", font=f2, fill=(220, 220, 220), anchor='mm')
    return im


def card(text):
    im = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((W / 2, H / 2), text, font=ImageFont.truetype(BOLD, 64), fill=(235, 235, 235), anchor='mm')
    return im


def endcard(rows, src):
    im = dark_bg(src); d = ImageDraw.Draw(im)
    d.text((W / 2, 640), rows[0], font=ImageFont.truetype(BOLD, 54), fill='white', anchor='mm', stroke_width=5, stroke_fill='black')
    d.text((W / 2, 760), rows[1], font=ImageFont.truetype(BOLD, 56), fill=(255, 200, 60), anchor='mm', stroke_width=4, stroke_fill='black')
    d.rounded_rectangle((170, 1300, 910, 1440), 30, fill=(200, 20, 30))
    d.text((W / 2, 1370), rows[2], font=ImageFont.truetype(BOLD, 54), fill='white', anchor='mm')
    d.text((W / 2, 1500), 'FOLLOW FOR THE NEXT EPISODE', font=ImageFont.truetype(BOLD, 36), fill=(220, 220, 220), anchor='mm')
    return im


def badge():
    p = os.path.join(B, 'badge.png')
    im = Image.new('RGBA', (W, 140), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(BOLD, 36)
    label = f"{EP['series']}  ·  EP {EP['episode']}"
    tw = d.textlength(label, font=f)
    d.rounded_rectangle((W / 2 - tw / 2 - 28, 40, W / 2 + tw / 2 + 28, 104), 18, fill=(0, 0, 0, 140))
    d.text((W / 2, 72), label, font=f, fill=(255, 255, 255), anchor='mm')
    im.save(p); return p


def captions(i, lines, phone_like):
    out = []
    font = ImageFont.truetype(BOLD, 62)
    for li, l in enumerate(lines):
        words, groups, cur = l['text'].split(), [], []
        for w_ in words:
            cur.append(w_)
            if len(cur) >= 5 or w_.endswith(('.', '?', ',', '!')):
                groups.append(' '.join(cur)); cur = []
        if cur:
            groups.append(' '.join(cur))
        wts = [len(g) + 3 for g in groups]
        tt = l['at']
        for k, g in enumerate(groups):
            dt = l['len'] * wts[k] / sum(wts)
            im = Image.new('RGBA', (W, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.text((W / 2, 120), g, font=font, fill=COLORS.get(l['who'], (255, 255, 255)), anchor='mm', stroke_width=7, stroke_fill='black')
            p = os.path.join(B, f'cap{i:02d}_{li}_{k}.png'); im.save(p)
            out.append((p, tt, tt + dt + (0.15 if k == len(groups) - 1 else 0)))
            tt += dt
    return out


# ---------- video segments ----------
BADGE = badge()
GRADE = "eq=brightness=-0.06:contrast=1.14:saturation=0.82:gamma=0.92,colorbalance=bs=0.07:bm=0.03:rh=0.02,vignette=PI/4.2,noise=alls=3:allf=t"
segs, last_v = [], None
for i, p in enumerate(plan):
    s, D_ = p['s'], p['dur']
    seg = os.path.join(B, f'seg{i:02d}.mp4')
    vid = s.get('v') and s['id'] or s.get('reuse')
    caps = captions(i, p['lines'], bool(s.get('phone')))
    cap_y = 1640 if (s.get('phone') or s.get('call') or s.get('end')) else 1430
    if vid:
        last_v = vid
        src = os.path.join(SHOTS_DIR, vid + '.mp4')
        slow = min(max(D_ / CLIP, 1.0), 1.6)
        chain = f"[0:v]setpts={slow:.3f}*PTS,minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:vsbmc=1,tpad=stop_mode=clone:stop_duration=10,scale={W}:{H}:flags=lanczos,{GRADE}"
        if s.get('flashback'):
            chain += ",hue=s=0.35,gblur=sigma=0.7,fade=t=in:st=0:d=0.35:color=white"
        inputs = ['-i', src]
    else:
        bgsrc = frame_of(last_v) if last_v else None
        if s.get('phone'):
            im = phone(s['phone'], bgsrc)
        elif s.get('call'):
            im = phone(None, bgsrc, call=s['call'])
        elif s.get('laptop'):
            im = laptop(s['laptop'], bgsrc)
        elif s.get('title'):
            im = title(s['title'])
        elif s.get('card'):
            im = card(s['card'])
        else:
            im = endcard(s['end'], frame_of(last_v, 4.5) if last_v else None)
        still = os.path.join(B, f'still{i:02d}.png'); im.save(still)
        n = int(D_ * FPS) + 2
        chain = (f"[0:v]scale={W*2}:{H*2},zoompan=z='1+0.06*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
                 "noise=alls=2:allf=t")
        inputs = ['-loop', '1', '-framerate', str(FPS), '-i', still]
    if s.get('title') or s.get('card'):
        chain += f",fade=t=in:st=0:d=0.4,fade=t=out:st={D_-0.35:.2f}:d=0.35"
    inputs += ['-i', BADGE]
    for c in caps:
        inputs += ['-i', c[0]]
    fc = chain + "[v0]"
    last = 'v0'
    if not s.get('title') and not s.get('card'):
        fc += f";[{last}][1:v]overlay=0:0[vb]"; last = 'vb'
    for k, c in enumerate(caps):
        fc += f";[{last}][{k+2}:v]overlay=0:{cap_y}:enable='between(t,{c[1]:.2f},{c[2]:.2f})'[c{k}]"; last = f'c{k}'
    fc += f";[{last}]trim=duration={D_:.2f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p[vout]"
    run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', fc, '-map', '[vout]', '-t', f'{D_:.2f}', '-an',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-r', str(FPS), seg])
    segs.append(seg)
    print('seg', i, s['id'], D_, flush=True)

# ---------- audio: voices ----------
N = int((TOTAL + 1.0) * SR)
voice = np.zeros(N, np.float32)
for p in plan:
    for l in p['lines']:
        a = load_audio(l['file'])
        a = a / (np.abs(a).max() + 1e-6) * 0.7
        st = int((p['start'] + l['at']) * SR)
        voice[st:st + len(a)] += a[:N - st]

# ---------- audio: score ----------
tt = np.arange(N) / SR
rng = np.random.default_rng(3)


def env_adsr(n, a=0.01, r=1.0):
    e = np.ones(n, np.float32)
    na = max(int(a * SR), 1)
    e[:na] = np.linspace(0, 1, na)
    return e * np.exp(-np.arange(n) / (r * SR)).astype(np.float32)


def tone(f, n, harm=(1, 0.35, 0.12)):
    x = np.arange(n) / SR
    return sum(h * np.sin(2 * np.pi * f * (k + 1) * x) for k, h in enumerate(harm)).astype(np.float32)


def add(buf, at, sig, g=1.0):
    st = int(at * SR)
    if st >= len(buf):
        return
    sig = sig[:len(buf) - st]
    buf[st:st + len(sig)] += g * sig


def lowpass(x, f):
    return sosfilt(butter(4, f, 'low', fs=SR, output='sos'), x).astype(np.float32)


IR_N = int(2.6 * SR)
ir = lowpass(rng.standard_normal(IR_N).astype(np.float32), 3500) * np.exp(-np.arange(IR_N) / (0.7 * SR)).astype(np.float32)
ir /= np.abs(ir).sum() / 6


def reverb(x, wet=0.35):
    return (x * (1 - wet) + wet * fftconvolve(x, ir)[:len(x)]).astype(np.float32)


NOTE = {'A2': 110, 'E3': 164.81, 'C3': 130.81, 'A3': 220, 'C4': 261.63, 'E4': 329.63, 'G#4': 415.3, 'A4': 440, 'B4': 493.88,
        'C5': 523.25, 'D#5': 622.25, 'E5': 659.25, 'F3': 174.61, 'G3': 196, 'D4': 293.66, 'F4': 349.23, 'G4': 392}


def bed(mood, a, b):
    n = int((b - a) * SR); x = np.zeros(n, np.float32); xt = np.arange(n) / SR
    drone = (0.30 * np.sin(2 * np.pi * 55 * xt) * (0.65 + 0.35 * np.sin(2 * np.pi * 0.09 * xt))
             + 0.18 * np.sin(2 * np.pi * 82.41 * xt) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.06 * xt + 1))).astype(np.float32)
    if mood in ('drone', 'hit', 'braam'):
        x += drone
    elif mood == 'silence':
        x += 0.25 * drone
    elif mood == 'piano':
        x += 0.5 * drone
        motif = ['A4', 'C5', 'E5', 'D#5', 'E4', 'A4', 'G#4', 'B4']
        k, at = 0, 0.2
        while at < b - a - 0.5:
            nn = int(2.2 * SR); add(x, at, tone(NOTE[motif[k % len(motif)]], nn) * env_adsr(nn, 0.005, 0.7), 0.22)
            k += 1; at += 1.15
    elif mood == 'sad':
        chords = [('A2', 'E3', 'C4', 'E4'), ('F3', 'C4', 'F4', 'A4'), ('C3', 'G3', 'E4', 'C5'), ('G3', 'D4', 'G4', 'B4')]
        at, k = 0.0, 0
        while at < b - a:
            nn = int(2.8 * SR); e = np.minimum(np.arange(nn) / (0.6 * SR), 1) * np.exp(-np.arange(nn) / (2.4 * SR))
            for q in chords[k % 4]:
                add(x, at, (np.sin(2 * np.pi * NOTE[q] * np.arange(nn) / SR) + 0.6 * np.sin(2 * np.pi * NOTE[q] * 1.003 * np.arange(nn) / SR)).astype(np.float32) * e, 0.07)
            add(x, at + 0.4, tone(NOTE[chords[k % 4][-1]] , int(1.8 * SR)) * env_adsr(int(1.8 * SR), 0.005, 0.6), 0.12)
            at += 2.4; k += 1
    elif mood == 'pulse':
        x += 0.6 * drone
        at, k = 0.0, 0
        while at < b - a:
            nn = int(0.25 * SR); add(x, at, tone(55 if k % 2 == 0 else 110, nn, (1, 0.4)) * env_adsr(nn, 0.004, 0.08), 0.35)
            if k % 4 == 2:
                add(x, at, tone(1760, int(0.06 * SR), (1,)) * env_adsr(int(0.06 * SR), 0.001, 0.015), 0.05)
            at += 60 / 104 / 2; k += 1
    elif mood in ('dread', 'riser'):
        x += 0.5 * drone
        for f, g in ((110, 0.10), (116.54, 0.08), (164.81, 0.05), (174.61, 0.04)):
            x += (g * np.sin(2 * np.pi * f * xt) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.21 * xt + f))).astype(np.float32)
        bpm = 72 if mood == 'dread' else 118
        at = 0.1
        while at < b - a:
            for off, g in ((0, 0.55), (0.16, 0.35)):
                nn = int(0.22 * SR); fr = 48 * np.exp(-np.arange(nn) / (0.08 * SR))
                add(x, at + off, (np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-np.arange(nn) / (0.06 * SR))).astype(np.float32), g)
            at += 60 / bpm
        if mood == 'riser':
            f = 150 * np.exp(np.log(6) * xt / max(b - a, 0.1))
            x += (0.18 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (xt / max(b - a, 0.1)) ** 2).astype(np.float32)
    return x


music = np.zeros(N, np.float32)
XF = 0.35
for i, p in enumerate(plan):
    a, b = p['start'], p['start'] + p['dur']
    x = bed(p['s'].get('mood', 'drone'), a, b + XF)
    n = len(x); e = np.ones(n, np.float32)
    nf = int(XF * SR)
    if i:
        e[:nf] = np.linspace(0, 1, nf)
    e[-nf:] = np.linspace(1, 0, nf)
    add(music, a, x * e)
    m = p['s'].get('mood')
    if m in ('hit', 'braam'):
        nn = int(3.0 * SR); xs = np.arange(nn) / SR
        boom = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-xs / 0.05)) / SR) * np.exp(-xs / 0.9)
        chord = sum(np.sin(2 * np.pi * f0 * h * xs) / h for f0 in (55, 82.41, 110, 130.81) for h in range(1, 7))
        sting = (0.9 * boom + 0.12 * chord * np.minimum(xs / 0.02, 1) * np.exp(-xs / (1.6 if m == 'braam' else 0.9))).astype(np.float32)
        add(music, a, lowpass(sting, 2500), 0.9)
music = reverb(music, 0.3)

# ---------- audio: effects ----------
sfx = np.zeros(N, np.float32)


def fx(kind):
    if kind == 'buzz':
        n = int(1.0 * SR); xs = np.arange(n) / SR
        am = ((xs % 0.5) < 0.32).astype(np.float32) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 28 * xs)))
        return lowpass((np.sin(2 * np.pi * 165 * xs) + 0.5 * np.sin(2 * np.pi * 330 * xs)).astype(np.float32) * am, 900) * 0.6
    if kind == 'bell':
        out = np.zeros(int(2.2 * SR), np.float32)
        for at, f in ((0, 659.25), (0.55, 523.25)):
            nn = int(1.6 * SR); add(out, at, tone(f, nn, (1, 0.3, 0.15, 0.05)) * env_adsr(nn, 0.003, 0.55), 0.6)
        return reverb(out, 0.3)
    if kind == 'key':
        out = np.zeros(int(1.2 * SR), np.float32)
        for at, fs, r in ((0, (2500, 3700), 0.02), (0.22, (2900, 4300), 0.02), (0.55, (1200, 2400, 3300), 0.05)):
            nn = int(0.15 * SR)
            add(out, at, sum(tone(f, nn, (1,)) for f in fs) * env_adsr(nn, 0.0005, r), 0.35)
        return out
    if kind == 'power':
        n = int(1.0 * SR); xs = np.arange(n) / SR
        f = 120 * np.exp(-xs * 1.6)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-xs / 0.5)).astype(np.float32) * 0.8
    return np.zeros(1, np.float32)


for p in plan:
    for kind, off in p['s'].get('sfx', []):
        add(sfx, p['start'] + off, fx(kind), 0.8)

# ---------- mix: the music dips under every voice ----------
venv = np.convolve(np.abs(voice), np.ones(int(0.05 * SR)) / int(0.05 * SR), 'same')
duck = (venv > 0.02).astype(np.float32)
duck = np.convolve(duck, np.ones(int(0.3 * SR)) / int(0.3 * SR), 'same')
mix = voice * 1.0 + music * 0.32 * (1 - 0.6 * duck) + sfx * 0.55
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix = mix / (np.abs(mix).max() + 1e-6) * 0.9
wav = os.path.join(B, 'mix.f32')
mix.astype(np.float32).tofile(wav)

# ---------- final: cuts joined, progress bar, sound ----------
lst = os.path.join(B, 'list.txt')
open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
out = os.path.join(D, f'ep{EPN}', f'episode{EPN}.mp4')
run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', wav,
     '-filter_complex', f"[0:v]drawbox=x=0:y=ih-14:w=iw*t/{TOTAL:.2f}:h=14:color=0xE01E28@0.95:t=fill[v];[1:a]aformat=channel_layouts=stereo[a]",
     '-map', '[v]', '-map', '[a]', '-t', f'{TOTAL:.2f}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
     '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out])
print('done', round(TOTAL, 1), 's', os.path.getsize(out))
