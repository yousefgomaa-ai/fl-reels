#!/usr/bin/env python3
"""VERSUS engine - "X vs Y vs Z: who makes it?" reels from a short JSON config (see stick/versus/*.json).

The heavy lifting lives in race.py (night lanes, following cameras, the run cycle, shaded figures, finish line) and
is reused here; a new reel is a ~40-line config: lanes (label, accessory, distance keyframes, actions, bubbles),
header text, counter label/scale, the licensed track and where its hit lands.

    python3 stick/versus.py stick/versus/mdo.json --stills      # 3 cheap stills (hook, middle, end) -> one sheet
    python3 stick/versus.py stick/versus/mdo.json               # the full reel -> stick/<name>.mp4

Config keys (all times in seconds):
  name, title (header), counter_label, counter_scale (counter = metres * scale), duration, bars_from (s),
  lanes: [{label, acc: band|cap|rich|none, road: straight|winding,
           dist: [[t, metres], ...]        piecewise-linear; 100 = finish
           acts: [[t, act], ...]          auto|stand|bent|sit|sit_phone|laugh|cheer|sad|grab_head|hop|limp|lie
           bubbles: [[t0, t1, "TEXT"]], marks: [[t, "!"]]}],
  lines: [[t, "CAPTION"], ...], winner: lane index,
  music: {file, hit_track, hit_video}  (licensed, in study/music; credit printed on render)
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import hq  # noqa
import race as R  # noqa
from race import K, S, FEET, PXM, START, FIN, RUN_SX, PWD, PHT, INK, GOLD  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa

W, H, FPS, SR = 1080, 1920, 30, 44100
MDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study", "music")
CFG = None
STAND = PW.STAND
LIE = dict(STAND, el=(-20, -80), hl=(-30, -40), er=(20, -80), hr=(30, -40))
POSES = {"stand": STAND, "bent": R.BENT, "sit": R.SIT_G, "sit_phone": R.SIT_PHONE, "laugh": R.LAUGH,
         "cheer": R.CHEER, "sad": R.C_SAD if hasattr(R, "C_SAD") else dict(STAND, head=(16, -136), neck=(8, -104)),
         "grab_head": R.GRAB_HEAD, "hop": R.HOP, "lie": LIE}
SITTING = {"sit", "sit_phone"}


# ---------------------------------------------------------------- per-lane motion
class Lane:
    def __init__(self, cfg, idx):
        self.c = cfg
        self.i = idx
        d = np.array(cfg["dist"], np.float64)
        self.kt, self.km = d[:, 0], d[:, 1]
        self.acts = cfg.get("acts", [[0, "auto"]])
        tg = np.arange(0, CFG["duration"] + 0.5, 1 / 240)
        m = np.interp(tg, self.kt, self.km)
        v = np.gradient(m, tg)
        L = (150 + 28 * np.abs(v)) / PXM
        self.tg, self.v = tg, v
        self.ph = np.concatenate([[0], np.cumsum(2 * np.pi * np.abs(v[:-1]) / L[:-1] * np.diff(tg))]) + 1.3 * idx

    def m(self, t):
        return float(np.interp(t, self.kt, self.km))

    def speed(self, t):
        return float(np.interp(t, self.tg, self.v))

    def phase(self, t):
        return float(np.interp(t, self.tg, self.ph))

    def act_at(self, t):
        cur, prev, t0 = self.acts[0][1], self.acts[0][1], 0.0
        for tt, a in self.acts:
            if t >= tt:
                prev, cur, t0 = cur, a, tt
        return prev, cur, t0

    def pose_of(self, act, t):
        v = self.speed(t)
        if act == "auto":
            if v > 2.0:
                return R.run_pose(self.phase(t), clamp(v / 9.0, 0.35, 1.0))
            if v > 0.3:
                return R.walk_pose(self.phase(t), 0.32)
            return STAND
        if act == "limp":
            p = R.walk_pose(2 * math.pi * t * 1.1, 0.28)
            return dict(p, head=(10, -146), neck=(6, -104))
        p = dict(POSES.get(act, STAND))
        b = 3 * math.sin(t * 5 + self.i)
        p["head"] = (p["head"][0], p["head"][1] + b)
        return p

    def hip_of(self, act, pose, x):
        if act in SITTING:
            return (x, FEET - 12 * S)
        if act == "lie":
            return (x, FEET - 16)
        return R.grounded(pose, x, FEET)

    def state(self, t):
        prev, cur, t0 = self.act_at(t)
        x = START + self.m(t) * PXM
        k = smooth(prog(t, t0, t0 + 0.3))
        p1, p2 = self.pose_of(prev, t), self.pose_of(cur, t)
        pose = lerp_pose(p1, p2, k) if k < 1 else p2
        h1, h2 = self.hip_of(prev, p1, x), self.hip_of(cur, p2, x)
        hip = (x, lerp(h1[1], h2[1], k))
        ang = (math.pi / 2) * (k if cur == "lie" else (1 - k if prev == "lie" else 0)) if "lie" in (prev, cur) else 0.0
        return pose, hip, ang, cur


LANES = []


def cam(lane, t):
    return max(0.0, START + LANES[lane].m(t) * PXM - RUN_SX)


# ---------------------------------------------------------------- panel / frame
SKY = None


def panel(t, i):
    ln = LANES[i]
    base = SKY[i].copy()
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = cam(i, t)
    vc = (cam(i, t + 0.01) - cam(i, t - 0.01)) / 0.02
    road = 1 if ln.c.get("road") == "winding" else (0 if i != 1 else 2)
    R.draw_world(d, road, c, vc)
    won = ln.m(t) >= 100
    t_cross = None
    if won:
        tt = np.linspace(0, CFG["duration"], 2000)
        t_cross = float(tt[np.argmax(np.interp(tt, ln.kt, ln.km) >= 100)])
    front = R.finish(d, road, c, t_cross, t)
    pose, hip, ang, act = ln.state(t)
    if road == 1:
        hip = (hip[0], hip[1] + (R.zig_y(hip[0]) - FEET))
    import ai_job as AJ
    pts = {k: (x - c, y) for k, (x, y) in AJ.place(pose, hip, 1, S, ang).items()}
    if act == "auto" and ln.speed(t) > 2:
        for j in range(3):
            u = ((ln.phase(t) / (2 * math.pi) * 2 + j / 3) % 1.0)
            px = pts["hip"][0] - 30 - 70 * u
            r = 5 + 12 * u
            d.ellipse([(px - r) * K, (FEET - r) * K, (px + r) * K, (FEET + r * 0.5) * K],
                      fill=(120, 130, 160, int(120 * (1 - u))))
    R.figure(d, pts, S, ln.c.get("acc", "none"), 1)
    if act == "sit_phone":
        R.phone_(d, pts["hr"][0] + 4, pts["hr"][1] - 10)
    if act in ("bent", "limp"):
        R.sweat(d, pts, t, 1)
    hx, hy = pts["head"]
    for t0, t1, txt in ln.c.get("bubbles", []):
        R.bubble(lay, t, t0, t1, txt, hx, hy - 36)
    for t0, mk in ln.c.get("marks", []):
        if t0 <= t < t0 + 0.8:
            k = hq.pop(t, t0, 0.2)
            R.text_c(d, hx + 6, hy - 50 - 30 * k, mk, 70 * k + 4, R.RED, stroke=4)
    R.front_pole(d, front)
    if won and t_cross is not None:
        R.hq.confetti(R._Pp(d), t, t_cross, t_cross + 0.6, max(200, FIN - c), 150, 5 + i, 50)
    g = lay.resize((lay.width // 4, lay.height // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
    glow = Image.new("RGBA", g.size, (150, 180, 255, 0))
    glow.putalpha(g.split()[3].point(lambda v: int(v * 0.5)))
    base.alpha_composite(glow.resize(lay.size, Image.BILINEAR))
    base.alpha_composite(lay)
    zo = 1 - smooth(prog(t, 0.0, 1.9))                 # the opening close-up
    focus = (pts["hip"][0] + 10, (pts["head"][1] + FEET) / 2)
    z = 1.0 + 0.03 * math.sin(math.pi * t / CFG["duration"]) + 0.85 * zo
    dx, dy = z * (PWD / 2 - focus[0]) * zo, z * (PHT / 2 - focus[1]) * zo
    im = hq.downsample(hq.camera(base, z, dx * K, dy * K), PWD, PHT)
    di = ImageDraw.Draw(im)
    f = font("Inter-SemiBold.otf", 32)
    x = 28
    for ch_ in ln.c["label"]:
        di.text((x + 2, 20), ch_, font=f, fill=(0, 0, 0, 160))
        di.text((x, 18), ch_, font=f, fill=(214, 220, 238, 255))
        x += f.getlength(ch_) + 9
    bar(im, i, t)
    di.rounded_rectangle([1, 1, PWD - 2, PHT - 2], 16, outline=(44, 54, 88, 255), width=3)
    return im


COLS = [(255, 70, 70), (70, 140, 255), GOLD, (120, 220, 140)]


def bar(im, i, t):
    t0 = CFG.get("bars_from", 4.0)
    if t < t0:
        return
    k = hq.pop(t, t0 + 0.08 * i, 0.3)
    m = min(100.0, LANES[i].m(t))
    d = ImageDraw.Draw(im)
    a = int(255 * min(1, k))
    y0 = 446 + 30 * (1 - min(1, k))
    x0, x1 = 24, PWD - 24
    d.rounded_rectangle([x0, y0, x1, y0 + 46], 12, fill=(6, 8, 20, int(215 * min(1, k))), outline=COLS[i] + (a,),
                        width=3)
    sc = CFG.get("counter_scale", 1.0)
    left = (100 - m) * sc
    lab = f"{left:.0f} {CFG.get('left_word', 'LEFT')}" if sc != 1 else f"{100 - m:.1f} M LEFT"
    d.text((x0 + 18, y0 + 8), lab, font=font("InterDisplay-Bold.otf", 27), fill=(240, 242, 250, a))
    tx0, tx1, ty = x0 + 270, x1 - 60, y0 + 23
    d.line([(tx0, ty), (tx1, ty)], fill=(70, 80, 110, a), width=6)
    px = lerp(tx0, tx1, m / 100)
    d.line([(tx0, ty), (px, ty)], fill=COLS[i] + (a,), width=6)
    d.ellipse([px - 11, ty - 11, px + 11, ty + 11], fill=(240, 242, 250, a), outline=COLS[i] + (a,), width=5)


def header(img, t):
    d = ImageDraw.Draw(img)
    lines = CFG.get("lines", [])
    if lines and t >= lines[0][0]:
        f = font("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", 46)
        for j, (t0, s) in enumerate(lines):
            if t >= t0:
                a = smooth(prog(t, t0, t0 + 0.35))
                PW.spaced(d, W / 2, 14 + j * 52, s, f, (246, 240, 226, int(255 * a)), 4)
    else:
        PW.spaced(d, W / 2, 18, CFG["title"], font("InterDisplay-Bold.otf", 70 if len(CFG["title"]) < 20 else 54),
                  (240, 242, 250, 255), 6)
    PW.spaced(d, W / 2, 112, CFG.get("counter_label", "DISTANCE ( M )"), font("Inter-SemiBold.otf", 26),
              (150, 158, 184, 255), 9)
    n = len(LANES)
    sc = CFG.get("counter_scale", 1.0)
    vals = [min(100.0, ln.m(t)) for ln in LANES]
    lead = max(range(n), key=lambda i: (vals[i], -i))
    win = CFG.get("winner")
    for i, ln in enumerate(LANES):
        cx = W * (i + 0.5) / n
        v = vals[i] * sc
        txt = f"{v:.0f}" if sc != 1 else (f"{v:.1f}" if v < 99.95 else "100")
        col = GOLD if (i == win and vals[i] >= 100) else ((245, 246, 252) if i == lead else (128, 136, 160))
        PW.spaced(d, cx, 144, txt, font("InterDisplay-Bold.otf", 84 if n <= 3 else 66), col + (255,), 2)
        PW.spaced(d, cx, 246, ln.c["label"], font("Inter-SemiBold.otf", 22 if n <= 3 else 18),
                  ((230, 232, 242) if i == lead else (128, 136, 160)) + (255,), 5)


BG = None


def frame(t):
    img = BG.copy()
    header(img, t)
    n = len(LANES)
    avail = H - 296 - 110
    sc = min(1.0, (avail - 8 * (n - 1)) / (n * PHT))
    ph = int(PHT * sc)
    y = 296
    for i in range(n):
        p = panel(t, i)
        if sc < 1:
            p = p.resize((int(PWD * sc), ph), Image.LANCZOS)
        img.alpha_composite(p, ((W - p.width) // 2, y))
        y += ph + 8
    return np.asarray(img.convert("RGB"))


def init_worker(path):
    global CFG, LANES, SKY, BG
    CFG = json.load(open(path))
    sc = CFG.get("counter_scale", 1.0)
    if sc != 1:
        R.SIGN_FMT = lambda mk: f"{CFG.get('counter_label', 'DAY').split()[0]} {int(mk * sc)}"
    LANES = [Lane(c, i) for i, c in enumerate(CFG["lanes"])]
    SKY = [R.make_sky(i) for i in range(len(LANES))]
    BG = Image.new("RGBA", (W, H), (7, 10, 24, 255))
    d = ImageDraw.Draw(BG)
    rng = np.random.default_rng(11)
    for _ in range(140):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(0.6, 1.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(210, 220, 255, int(rng.uniform(40, 170))))


def render(i):
    return frame(i / FPS).tobytes()


# ---------------------------------------------------------------- sound
def audio():
    dur = CFG["duration"]
    n = int(dur * SR)
    out = np.zeros((n, 2))
    mu = CFG.get("music")
    if mu:
        start = max(0.0, mu["hit_track"] - mu["hit_video"])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i",
                              os.path.join(MDIR, mu["file"]), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                             capture_output=True).stdout
        m = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
        out[:min(n, len(m))] += m[:n] * np.minimum(1, np.arange(min(n, len(m))) / (0.15 * SR))[:, None]
        tt = np.arange(n) / SR
        out *= np.clip((dur - tt) / 0.6, 0.15, 1)[:, None]
    mix_in(out, noise(0.4, 1, lo=200, hi=8000)[:int(0.4 * SR)] * env(int(0.4 * SR), 0.0005, 0.07), 0.0, 0.3)
    for i, ln in enumerate(LANES):
        last = None
        for j in range(len(ln.tg)):
            if ln.tg[j] > dur:
                break
            k = int(ln.ph[j] // math.pi)
            if last is not None and k != last and abs(ln.v[j]) > 1.0:
                at = ln.tg[j]
                mix_in(out, tone(180 + 30 * i, 0.06, (1, 0.5), a=0.001, d=0.02), at, 0.04, (i - 1) * 0.4)
            last = k
        for t0, _ in ln.c.get("marks", []):
            mix_in(out, tone(1320, 0.12, (1, 0.4), a=0.002, d=0.06), t0, 0.05)
        if ln.m(dur) >= 100:
            tt = np.linspace(0, dur, 2000)
            tc = float(tt[np.argmax(np.interp(tt, ln.kt, ln.km) >= 100)])
            mix_in(out, tone(1200, 0.08, (1, 0.5), a=0.001, d=0.03, sweep=600), tc, 0.1)
    m = int(0.25 * SR)
    k = np.linspace(0, 1, m)[:, None]
    out[-m:] = out[-m:] * (1 - k) + out[:m] * k
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    path = sys.argv[1]
    init_worker(path)
    name = CFG["name"]
    here = os.path.dirname(os.path.abspath(__file__))
    if "--stills" in sys.argv:
        dur = CFG["duration"]
        ts = [0.0, dur * 0.5, dur - 1.0]
        ims = [Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS) for t in ts]
        sheet = Image.new("RGB", (1080, 640))
        for j, im in enumerate(ims):
            sheet.paste(im, (j * 360, 0))
        outp = os.path.join(here, "versus", f"{name}-stills.png")
        sheet.save(outp)
        print(outp)
        return
    out = os.path.join(here, f"{name}.mp4")
    wav = out + ".wav"
    write_wav(wav, audio())
    nf = int(round(CFG["duration"] * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init_worker, initargs=(path,)) as pool:
        for i, b in enumerate(pool.imap(render, range(nf), chunksize=2)):
            p.stdin.write(b)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)
    mu = CFG.get("music")
    if mu:
        print(f'Credit: Music: "{mu["file"][:-4]}" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
