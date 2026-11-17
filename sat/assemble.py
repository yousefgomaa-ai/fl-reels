# Satisfying sample edit (owner, 2026-11-18): six impossible cuts, numbered, the hook question on top, a progress bar,
# a vote card at the end over all six; sound made here from tones and short bursts (no steady noise bed: the hiss
# the owner heard on the reels, 2026-11-11).
import json, os, subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
from PIL import Image, ImageDraw, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(D, 'sample.json')))
CL, B = os.path.join(D, 'out', 'clips'), os.path.join(D, 'build')
os.makedirs(B, exist_ok=True)
W, H, FPS, SR = 1080, 1920, 30, 44100
CLIP, END = 4.5, 4.0
clips = [c for c in J['clips'] if os.path.exists(os.path.join(CL, c['id'] + '.mp4'))]
TOTAL = CLIP * len(clips) + END
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def font(n):
    return ImageFont.truetype(BOLD, n)
def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-2000:])

def text_png(path, lines, size=(W, 420)):
    im = Image.new('RGBA', size, (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = 20
    for txt, n, col in lines:
        f = font(n)
        d.text((size[0] // 2, y), txt, font=f, fill=col, anchor='ma', stroke_width=max(3, n // 12), stroke_fill='black')
        y += int(n * 1.25)
    im.save(path)

def badge(path, num, label):
    im = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((W // 2 - 70, 0, W // 2 + 70, 140), fill=(255, 214, 0), outline='black', width=6)
    d.text((W // 2, 70), str(num), font=font(96), fill='black', anchor='mm')
    d.text((W // 2, 200), label, font=font(54), fill='white', anchor='mm', stroke_width=5, stroke_fill='black')
    im.save(path)

# ---------- clips ----------
hook = os.path.join(B, 'hook.png')
text_png(hook, [("WHICH ONE IS THE", 62, 'white'), ("MOST SATISFYING?", 76, (255, 214, 0)), ("watch till the end", 40, (220, 220, 220))])
segs = []
LOOK = "scale=-2:1920:flags=lanczos,crop=1080:1920,unsharp=5:5:0.6,eq=contrast=1.06:saturation=1.12,fps=30"
for i, c in enumerate(clips):
    bp = os.path.join(B, f"b{i}.png"); badge(bp, i + 1, c['label'])
    seg = os.path.join(B, f"seg{i}.mp4")
    fc = (f"[0:v]{LOOK},trim=duration={CLIP},setpts=PTS-STARTPTS[v];"
          f"[v][1:v]overlay=0:150[h];[h][2:v]overlay=0:1450,fade=t=in:st=0:d=0.15[o]")
    run(['ffmpeg', '-y', '-v', 'error', '-i', os.path.join(CL, c['id'] + '.mp4'), '-i', hook, '-i', bp, '-filter_complex', fc,
         '-map', '[o]', '-t', str(CLIP), '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-r', str(FPS), seg])
    segs.append(seg); print('clip', i + 1, c['id'], flush=True)

# ---------- end card: all six in a grid, the vote ----------
grid = os.path.join(B, 'grid.mp4')
n = len(clips)
cols, rows = 3, (n + 2) // 3
tw, th = W // cols, int(W // cols * 16 / 9 * 0.82)
ins, parts = [], []
for i, c in enumerate(clips):
    ins += ['-i', os.path.join(CL, c['id'] + '.mp4')]
    nb = os.path.join(B, f"n{i}.png")
    im = Image.new('RGBA', (90, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, 88, 88), fill=(255, 214, 0), outline='black', width=4); d.text((44, 44), str(i + 1), font=font(56), fill='black', anchor='mm')
    im.save(nb); ins += ['-i', nb]
    parts.append(f"[{2*i}:v]scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th},fps=30,trim=duration={END},setpts=PTS-STARTPTS[t{i}];"
                 f"[t{i}][{2*i+1}:v]overlay=12:12[g{i}]")
lay = '|'.join(f"{(i % cols) * tw}_{(i // cols) * th}" for i in range(n))
endtxt = os.path.join(B, 'end.png')
text_png(endtxt, [("COMMENT YOUR NUMBER", 66, (255, 214, 0)), ("1  2  3  4  5  6", 60, 'white'), ("FOLLOW FOR MORE IMPOSSIBLE CUTS", 36, (220, 220, 220))], (W, 330))
ins += ['-f', 'lavfi', '-i', f"color=c=0x0b0b0f:s={W}x{H}:r=30:d={END}", '-i', endtxt]
fc = ';'.join(parts) + f";{''.join(f'[g{i}]' for i in range(n))}xstack=inputs={n}:layout={lay}[gr];" \
     f"[{2*n}:v][gr]overlay=0:{(H - rows * th) // 2 - 120}[bg];[bg][{2*n+1}:v]overlay=0:{(H + rows * th) // 2 - 80},fade=t=in:st=0:d=0.3[o]"
run(['ffmpeg', '-y', '-v', 'error', *ins, '-filter_complex', fc, '-map', '[o]', '-t', str(END), '-an', '-c:v', 'libx264',
     '-preset', 'medium', '-crf', '19', '-r', str(FPS), grid])
segs.append(grid)
lst = os.path.join(B, 'list.txt'); open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
silent = os.path.join(B, 'silent.mp4')
run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent])

# ---------- sound ----------
rng = np.random.default_rng(5)
N = int((TOTAL + 0.5) * SR)
def band(x, lo, hi):
    return sosfilt(butter(4, [lo, hi], 'band', fs=SR, output='sos'), x).astype(np.float32)
def env(n, a, r):
    e = np.ones(n, np.float32); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    return e * np.exp(-np.arange(n) / (r * SR)).astype(np.float32)
def burst(dur, lo, hi, a=0.002, r=0.05):
    n = int(dur * SR); return band(rng.standard_normal(n).astype(np.float32), lo, hi) * env(n, a, r)
def ping(f, dur=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * env(n, 0.001, dur / 4)).astype(np.float32)
def put(buf, at, x, g=1.0):
    s = int(at * SR); e = min(N, s + len(x)); buf[s:e] += x[:e - s] * g

fx = np.zeros(N, np.float32)
for i, c in enumerate(clips):
    t0 = i * CLIP; kind = c.get('snd', 'squish')
    if kind == 'glass':      # crisp crackles, then glass pings as it splits
        for k in range(26):
            put(fx, t0 + 0.8 + k * 0.06 + rng.random() * 0.03, burst(0.04, 2500, 9000, r=0.012), 0.5)
        for k in range(9):
            put(fx, t0 + 2.4 + rng.random() * 1.6, ping(2600 + rng.random() * 3800), 0.18)
    elif kind == 'crack':    # a crust breaking: low cracks and a warm rumble
        for k in range(14):
            put(fx, t0 + 0.9 + rng.random() * 2.8, burst(0.09, 180, 2200, r=0.03), 0.7)
        put(fx, t0 + 1.4, burst(2.4, 40, 160, a=0.4, r=1.2), 0.5)
    elif kind == 'squish':   # a soft wet slice
        for k in range(10):
            put(fx, t0 + 0.9 + k * 0.17, burst(0.22, 300, 1600, a=0.03, r=0.08), 0.45)
    elif kind == 'crush':    # crunch that builds, then a shatter of pings
        for k in range(40):
            put(fx, t0 + 0.6 + (k / 40) ** 0.7 * 2.2, burst(0.05, 800, 7000, r=0.015), 0.25 + 0.5 * k / 40)
        for k in range(14):
            put(fx, t0 + 2.9 + rng.random() * 1.2, ping(3000 + rng.random() * 4000, 0.4), 0.15)
    put(fx, t0, burst(0.12, 60, 400, r=0.04), 0.35)  # a soft knock on each new clip
# Soft music bed: slow warm chords, low under the sounds.
t = np.arange(N) / SR
mus = np.zeros(N, np.float32)
chords = [(220.0, 277.18, 329.63), (196.0, 246.94, 293.66), (174.61, 220.0, 261.63), (196.0, 246.94, 329.63)]
for k in range(int(TOTAL // 4) + 1):
    for f in chords[k % 4]:
        n = int(4.4 * SR); tt = np.arange(n) / SR
        x = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.minimum(1, tt / 0.8) * np.exp(-tt / 3.5)
        put(mus, k * 4.0, x.astype(np.float32), 0.06)
# the vote card: a bright rising chime
for k, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
    put(fx, TOTAL - END + 0.1 + k * 0.09, ping(f, 1.2), 0.25)
mix = fx + mus
mix = mix / (np.abs(mix).max() + 1e-6) * 0.89
wav = os.path.join(B, 'mix.wav'); wavfile.write(wav, SR, (mix * 32767).astype(np.int16))

# ---------- final: progress bar + sound ----------
out = os.path.join(D, 'satisfying_sample.mp4')
run(['ffmpeg', '-y', '-v', 'error', '-i', silent, '-i', wav, '-filter_complex',
     f"[0:v]drawbox=x=0:y=ih-14:w=iw*t/{TOTAL:.2f}:h=14:color=0xffd600:t=fill[v]", '-map', '[v]', '-map', '1:a',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out])
print('done', round(TOTAL, 1), 's', os.path.getsize(out))
