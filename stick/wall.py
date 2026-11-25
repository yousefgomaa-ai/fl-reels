#!/usr/bin/env python3
"""SAME WALL - "Who's still building on Day 365?" One night scene, three builders side by side, 20 s, loops.

MOTIVATION lays a few bricks and sits down ("I'LL FINISH IT MONDAY."). DISCIPLINE (red scarf) lays one row after
another, every day, the wall growing neat and straight. OBSESSION builds three times faster, the bricks crooked, his
wall leaning more and more - it collapses around day 300. Rain, then snow, pass over them. Day 365: one wall standing.
ONE BRICK A DAY. / EVERY DAY.  Loops back to DAY 1.

    python3 stick/wall.py --stills          # 3 frames -> stick/versus/wall-stills.png
    python3 stick/wall.py stick/wall.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import ai_job as AJ  # noqa
import hq  # noqa
import compare as C  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H, INK, BODY  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa

FPS, SR = 30, 44100
DUR = 20.0
NF = int(round(DUR * FPS))
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
MDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study", "music")
STAND = PW.STAND
T365 = 17.6
T_COLLAPSE = 14.6
T_LINES = 18.0
WALL_X = [235, 565, 895]
BW, BH = 34, 17                    # brick size
COLS = 4                           # bricks per row
LABELS = ["MOTIVATION", "DISCIPLINE", "OBSESSION"]
ORANGE = (255, 140, 40)
BRICK = (170, 82, 60)


def day(t):
    if t >= T365:
        return 365
    u = t / T365
    return max(1, int(round(1 + 364 * (u ** 1.35))))


# bricks laid (the counter), and rows shown (the picture)
def bricks(i, t):
    d = day(t)
    if i == 0:
        return min(8, int(t / 0.3) + 1) if t < 2.6 else 8
    if i == 1:
        return d * 10
    if t >= T_COLLAPSE:
        return int(day(T_COLLAPSE) * 30)
    return d * 30


def rows_shown(i, t):
    if i == 0:
        return bricks(0, t) / COLS
    if i == 1:
        return min(34, 2 + 32 * (day(t) / 365) ** 0.8)
    return min(40, 2 + 44 * (day(min(t, T_COLLAPSE)) / 365) ** 0.6)


def lean(t):
    return 0.0 if t < 3 else min(0.28, 0.02 + 0.26 * ((t - 3) / (T_COLLAPSE - 3)) ** 2)


# ---------------------------------------------------------------- drawing
def wall(d, i, t):
    x0 = WALL_X[i] - COLS * BW / 2
    rows = rows_shown(i, t)
    nfull = int(rows)
    part = rows - nfull
    rng = np.random.default_rng(i + 3)
    ang = lean(t) if i == 2 else 0.0
    for r in range(nfull + 1):
        nb = COLS if r < nfull else int(round(part * COLS))
        for c in range(nb):
            off = BW / 2 if r % 2 else 0
            bx = x0 + c * BW + off - (BW / 2 if r % 2 and c == COLS - 1 else 0)
            by = FLOOR - (r + 1) * BH
            jx = jy = 0.0
            if i == 2:
                jx, jy = rng.uniform(-6, 6), rng.uniform(-3, 3)
                h = FLOOR - by
                bx += h * math.sin(ang) + jx
            col = tuple(int(v * (0.85 + 0.25 * rng.uniform())) for v in BRICK)
            rrect(d, (bx + 1, by + 1 + jy, bx + BW - 1, by + BH - 1 + jy), 2, col + (255,), outline=(60, 30, 22, 255), w=1.5)
    return FLOOR - (nfull + (1 if part > 0 else 0)) * BH, x0


def collapse(d, t):
    """Obsession's wall coming down"""
    u = t - T_COLLAPSE
    rows = int(rows_shown(2, T_COLLAPSE))
    rng = np.random.default_rng(9)
    x0 = WALL_X[2] - COLS * BW / 2
    ang = lean(T_COLLAPSE)
    for r in range(rows):
        for c in range(COLS):
            h = (r + 1) * BH
            bx = x0 + c * BW + h * math.sin(ang)
            by = FLOOR - h
            delay = (rows - r) * 0.012
            v = max(0.0, u - delay)
            vx = rng.uniform(40, 220)
            nx = bx + vx * v
            ny = min(FLOOR - BH - rng.uniform(0, 30), by + 900 * v * v)
            rot = rng.uniform(-3, 3) * v
            c_, s_ = math.cos(rot), math.sin(rot)
            pts = [(-BW / 2, -BH / 2), (BW / 2, -BH / 2), (BW / 2, BH / 2), (-BW / 2, BH / 2)]
            poly(d, [(nx + BW / 2 + px * c_ - py * s_, ny + BH / 2 + px * s_ + py * c_) for px, py in pts],
                 BRICK + (255,), outline=(60, 30, 22, 255), w=1.5)
    if u < 1.2:
        for j in range(20):
            a = rng.uniform(0, 6.28)
            rr = 40 + 260 * u
            ell(d, WALL_X[2] + 60 + rr * math.cos(a), FLOOR - 40 + rr * 0.3 * math.sin(a), 18 + 30 * u, 12 + 20 * u,
                (150, 140, 130, int(150 * (1 - u / 1.2))))


SIT_PHONE = {"head": (4, -134), "neck": (0, -96), "el": (26, -56), "hl": (46, -78), "er": (22, -52), "hr": (42, -74),
             "kl": (52, -38), "fl": (104, -2), "kr": (46, -32), "fr": (100, 2)}
KNEEL = {"head": (30, -120), "neck": (20, -84), "el": (30, -40), "hl": (40, 4), "er": (24, -36), "hr": (34, 8),
         "kl": (40, 6), "fl": (-10, 60), "kr": (-20, 54), "fr": (-70, 60)}


def builder(stage, d, i, t, top):
    s = 0.95
    x = WALL_X[i] - 120
    if i == 0 and t >= 2.6:
        k = smooth(prog(t, 2.6, 3.1))
        pose = lerp_pose(STAND, SIT_PHONE, k)
        hip = (x - 20, lerp(FLOOR - 113 * s, FLOOR - 12 * s, k))
        pts = place(pose, hip, 1, s)
        figure(stage, pts, s, light=(0.4, -0.9))
        if k > 0.6:
            hx, hy = pts["hr"]
            rrect(d, (hx - 7, hy - 22, hx + 9, hy + 4), 3, (18, 18, 24, 255))
            rrect(d, (hx - 5, hy - 19, hx + 7, hy + 1), 2, (150, 190, 255, 255))
        return pts
    if i == 2 and t >= T_COLLAPSE:
        k = smooth(prog(t, T_COLLAPSE + 0.4, T_COLLAPSE + 1.0))
        pose = lerp_pose(STAND, KNEEL, k)
        hip = (x, lerp(FLOOR - 113 * s, FLOOR - 62 * s, k))
        pts = place(pose, hip, 1, s)
        figure(stage, pts, s, light=(0.4, -0.9))
        return pts
    # laying bricks: lift a brick from the pile, reach to the top of the wall, set it down
    rate = {0: 3.3, 1: 1.7, 2: 4.2}[i]
    ph = (t * rate) % 1.0
    reach_y = max(top, FLOOR - 250 * s)
    lift = math.sin(math.pi * ph)
    hand = (lerp(x + 40, WALL_X[i] - 30, ph), lerp(FLOOR - 70, reach_y - 8, lift))
    pose = dict(STAND, head=(10 + 8 * lift, -150 - 6 * lift))
    pts = place(pose, (x, FLOOR - 113 * s), 1, s)
    pts = dict(pts)
    for side, dy in (("r", 0), ("l", 12)):
        tgt = (hand[0] - (6 if side == "l" else 0), hand[1] + dy)
        pts["h" + side] = tgt
        pts["e" + side] = ik(pts["neck"], tgt, 42 * s, 40 * s, 1)
    figure(stage, pts, s, light=(0.4, -0.9), scarf=(i == 1), back=-1)
    rrect(d, (hand[0] - BW / 2, hand[1] - BH, hand[0] + BW / 2, hand[1]), 2, BRICK + (255,), outline=(60, 30, 22, 255),
          w=1.5)
    if i == 2:
        for side in ("hl", "hr"):
            hx, hy = pts[side]
            ell(d, hx, hy, 14, 14, ORANGE + (90,))
    # the pile of bricks at his feet
    for j in range(3):
        rrect(d, (x - 70 + j * 18, FLOOR - BH * (j + 1) + 2, x - 70 + j * 18 + BW, FLOOR - BH * j), 2, BRICK + (255,),
              outline=(60, 30, 22, 255), w=1.5)
    return pts


def weather(d, t):
    dd = day(t)
    rain = smooth(clamp((dd - 80) / 15)) * (1 - smooth(clamp((dd - 150) / 15)))
    snow = smooth(clamp((dd - 245) / 15)) * (1 - smooth(clamp((dd - 330) / 15)))
    rng = np.random.default_rng(4)
    if rain > 0.01:
        for j in range(150):
            x0, sp = rng.uniform(-60, W + 60), rng.uniform(1.0, 1.4)
            y = ((t * sp * 1.6 + rng.uniform(0, 1)) % 1.0) * (FLOOR + 60) - 40
            line(d, [(x0 - 0.15 * y, y), (x0 - 0.15 * y - 6, y + 34)], (150, 170, 210, int(140 * rain)), 1.6)
    if snow > 0.01:
        for j in range(140):
            x0, sp, ph = rng.uniform(-40, W + 40), rng.uniform(0.08, 0.16), rng.uniform(0, 1)
            y = ((t * sp + ph) % 1.0) * (FLOOR + 40) - 20
            r = rng.uniform(2, 4.2)
            ell(d, x0 + 18 * math.sin(t * 0.8 + ph * 6), y, r, r, (236, 240, 250, int(220 * snow)))


def frame(t):
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(stage)
    tops = []
    for i in range(3):
        if i == 2 and t >= T_COLLAPSE:
            collapse(d, t)
            tops.append(FLOOR)
        else:
            top, _ = wall(d, i, t)
            tops.append(top)
    for i in range(3):
        builder(stage, d, i, t, tops[i])
    if 4.4 <= t < 7.0:
        C_bubble = getattr(sys.modules[__name__], "_bubble")
        C_bubble(stage, t, 4.4, 7.0, "I'LL FINISH IT MONDAY.", WALL_X[0] - 40, FLOOR - 220)
    weather(d, t)
    spots = ((WALL_X[0], 0.7), (WALL_X[1], 1.0), (WALL_X[2], 0.8))
    base = C.stage_bg(spots).copy()
    C.dust(ImageDraw.Draw(base), t, spots, seed=1, n=30)
    tp = stage.crop((0, 0, W * K, FLOOR * K))
    refl = tp.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, W * K, (H - FLOOR) * K))
    refl = refl.resize((W * K // 4, (H - FLOOR) * K // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    refl = refl.resize((W * K, (H - FLOOR) * K), Image.BILINEAR)
    fade = np.linspace(0.3, 0.0, (H - FLOOR) * K, dtype=np.float32)[:, None]
    refl.putalpha(Image.fromarray((np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)))
    base.alpha_composite(refl, (0, FLOOR * K))
    base.alpha_composite(stage)
    sh = 0.0
    if T_COLLAPSE <= t < T_COLLAPSE + 0.5:
        sh = 14 * (1 - (t - T_COLLAPSE) / 0.5)
    z = 1.08
    im = hq.camera(base, z, sh * math.sin(t * 90) * K, (z * (H / 2 - 1080) + sh * 0.6 * math.cos(t * 77)) * K)
    im = im.resize((W, H), Image.LANCZOS)
    header(im, t)
    return np.asarray(im.convert("RGB"))


def _bubble(layer, t, t0, t1, s, x, y):
    import race
    race.bubble(layer, t, t0, t1, s, x, y, size=26)


def header(im, t):
    d = ImageDraw.Draw(im)
    if t < T_LINES:
        PW.spaced(d, W / 2, 34, "WHO'S STILL BUILDING ON DAY 365?", font("InterDisplay-Bold.otf", 44),
                  (236, 238, 246, 255), 3)
    else:
        f = font(SERIF_B, 56)
        for j, s in enumerate(("ONE BRICK A DAY.", "EVERY DAY.")):
            a = smooth(prog(t, T_LINES + 0.6 * j, T_LINES + 0.6 * j + 0.35))
            PW.spaced(d, W / 2, 18 + j * 64, s, f, (246, 240, 226, int(255 * a)), 5)
    dd = day(t)
    k = 1.0
    PW.spaced(d, W / 2, 150, f"DAY {dd}", font("InterDisplay-Bold.otf", 110), (246, 246, 250, 255), 6)
    for i in range(3):
        cx = WALL_X[i]
        n = bricks(i, t)
        dead = i == 2 and t >= T_COLLAPSE
        col = (128, 136, 160) if i == 0 else ((246, 200, 90) if i == 1 and t >= T365 else
                                              ((236, 120, 90) if dead else (236, 238, 246)))
        PW.spaced(d, cx, 300, LABELS[i], font("Inter-SemiBold.otf", 24),
                  (ORANGE if i == 2 else (214, 220, 238)) + (255,), 6)
        PW.spaced(d, cx, 334, f"{n:,}" if not dead else "0", font("InterDisplay-Bold.otf", 52), col + (255,), 2)
        PW.spaced(d, cx, 396, "BRICKS" if not dead else "FELL", font("Inter-SemiBold.otf", 18), (128, 136, 160, 255), 5)


def render(i):
    return frame(i / FPS).tobytes()


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(max(0.0, MUSIC_HIT - T365)), "-t", str(DUR), "-i",
                          os.path.join(MDIR, MUSIC_FILE), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    m = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    out[:min(n, len(m))] += m[:n] * np.minimum(1, np.arange(min(n, len(m))) / (0.15 * SR))[:, None]
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.6, 0.15, 1)[:, None]
    for i, rate in enumerate((3.3, 1.7, 4.2)):
        k = 0
        while True:
            at = (k + 0.98) / rate
            k += 1
            if at >= DUR:
                break
            if (i == 0 and at > 2.6) or (i == 2 and at > T_COLLAPSE):
                continue
            mix_in(out, tone(320 - 40 * i, 0.08, (1, 2.1), a=0.001, d=0.03) * 0.8, at, 0.04, (i - 1) * 0.5)
    mix_in(out, noise(1.4, 5, lo=60, hi=2500)[:int(1.4 * SR)] * env(int(1.4 * SR), 0.005, 0.5), T_COLLAPSE, 0.35, 0.5)
    for j in range(10):
        mix_in(out, tone(260 + 30 * j, 0.06, (1, 2.1), a=0.001, d=0.02), T_COLLAPSE + 0.2 + j * 0.07, 0.05, 0.5)
    m = int(0.25 * SR)
    k = np.linspace(0, 1, m)[:, None]
    out[-m:] = out[-m:] * (1 - k) + out[:m] * k
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


MUSIC_FILE = "The Escalation.mp3"
MUSIC_HIT = 280.0


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--stills" in sys.argv:
        ts = [0.0, 10.0, DUR - 1.0]
        sheet = Image.new("RGB", (1080, 640))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS), (j * 360, 0))
        p = os.path.join(here, "versus", "wall-stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "wall.mp4")
    wav = out + ".wav"
    write_wav(wav, audio())
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for b in pool.imap(render, range(NF), chunksize=2):
            p.stdin.write(b)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)
    print(f'Credit: Music: "{MUSIC_FILE[:-4]}" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
