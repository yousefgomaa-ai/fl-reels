#!/usr/bin/env python3
"""Symbolic #5 - IT'S NOT WHAT YOU EARN. IT'S WHAT YOU KEEP. Split screen, 14 s, loops. Minimal symbolic style.

Hook (frame 0): below, a huge pipe pours a river of coins into a bucket full of holes - coins spray out of every
hole; above, a small pipe drips coins into a bucket with no holes. Below, the pipe gets bigger ($5K -> $9K) and
right away new holes open (TAKEOUT, SUBSCRIPTIONS, SHOPPING, NEW CAR, BIGGER HOUSE). Above, the bucket slowly fills.
Twist at ~65%: above it is full and glowing - SAVED $36,000 - below it is dry - SAVED $0.
"IT'S NOT WHAT YOU EARN. / IT'S WHAT YOU KEEP."  FOLLOW FOR MORE.

    python3 stick/leaky_bucket.py stick/leaky-bucket.mp4
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
import game_spend as GS  # noqa
import one_call as OC  # noqa
import five_minutes as FM  # noqa
import music  # noqa
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          prog, smooth, spaced, tone, write_wav)

MUSIC = "piano_c"
W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 14.0
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
FIG, FIG_FAR = AJ.DOER, AJ.DOER_FAR
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141
GOLD = (245, 196, 60)
GOLD_D = (200, 150, 30)

BK = (640, 330, 320, 290)        # bucket: centre x, top y, top width, height
PIPE_X = 640
T_RAISE = 3.6
HOLES = [(-80, 70, "TAKEOUT", -1.0), (70, 115, "SUBSCRIPTIONS", -1.0), (-50, 160, "SHOPPING", 1.8),
         (80, 205, "NEW CAR", T_RAISE + 0.4), (-20, 250, "BIGGER HOUSE", 5.4)]
T_FULL = 8.6                     # the twist
T_L1, T_L2 = 10.8, 11.8
CPS = 18.0
LINE1, LINE2 = "IT'S NOT WHAT YOU EARN.", "IT'S WHAT YOU KEEP."
T_FOLLOW = 12.8


def level(t, top):
    if top:
        return 0.05 + 0.95 * smooth(prog(t, 0.0, T_FULL)) ** 0.9
    return 0.08 + 0.04 * math.sin(t * 3) if t < T_FULL else 0.0 + 0.02 * (1 - prog(t, T_FULL, T_FULL + 0.6))


def bucket_poly(level_k=1.0):
    cx, ty, tw, h = BK
    bw = tw * 0.78
    by = ty + h
    if level_k >= 1:
        return [(cx - tw / 2, ty), (cx + tw / 2, ty), (cx + bw / 2, by), (cx - bw / 2, by)]
    y = by - h * level_k
    w = lerp(bw, tw, level_k)
    return [(cx - w / 2, y), (cx + w / 2, y), (cx + bw / 2, by), (cx - bw / 2, by)]


def hole_pos(hx, hy):
    cx, ty, tw, h = BK
    return cx + hx, ty + hy


# ---------------------------------------------------------------- poses
STAND = PW.STAND
HIPS = dict(STAND, el=(-34, -70), hl=(-6, -40), er=(34, -70), hr=(6, -40))
CHEER = dict(STAND, head=(0, -152), el=(-30, -120), hl=(-40, -170), er=(30, -120), hr=(40, -170))
PANIC = dict(STAND, head=(10, -146), el=(40, -90), hl=(70, -70), er=(30, -96), hr=(64, -80))
PEER = dict(STAND, head=(40, -134), neck=(26, -98), el=(56, -90), hl=(90, -96), er=(50, -84), hr=(84, -90))


def person(t, top):
    hip = (300, STAND_Y)
    if top:
        if t < T_FULL:
            return lerp_pose(STAND, HIPS, 0.8), hip, 1
        k = smooth(prog(t, T_FULL, T_FULL + 0.4))
        return lerp_pose(HIPS, CHEER, k), hip, 1
    if t < T_RAISE:
        return lerp_pose(STAND, PANIC, 0.5 + 0.5 * math.sin(t * 6)), hip, 1
    if t < T_RAISE + 0.6:
        k = math.sin(math.pi * prog(t, T_RAISE, T_RAISE + 0.6))
        return lerp_pose(STAND, CHEER, k), hip, 1
    if t < T_FULL:
        return lerp_pose(PANIC, dict(PANIC, hl=(80, -40)), 0.5 + 0.5 * math.sin(t * 8)), hip, 1
    k = smooth(prog(t, T_FULL, T_FULL + 0.4))
    return lerp_pose(STAND, PEER, k), (lerp(300, 380, k), STAND_Y), 1


# ---------------------------------------------------------------- drawing
def build_bg():
    yy = np.mgrid[0:PH, 0:W][0].astype(np.float32)
    g = np.clip(4 + yy / PH * 16, 0, 255)
    img = np.stack([g, g, g + 4], -1)
    img = np.where((yy > FYP)[..., None], img * 0.6 + 10, img)
    im = Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")
    ImageDraw.Draw(im).line([(0, FYP), (W, FYP)], fill=(50, 50, 56, 255), width=2)
    return im


def coin(d, x, y, r=9, a=255):
    d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=GOLD + (a,), outline=GOLD_D + (a,), width=2)


def draw_pipe(d, t, top):
    ink = INK + (255,)
    big = 0 if top else (1 if t < T_RAISE else 1 + smooth(prog(t, T_RAISE, T_RAISE + 0.4)))
    pw = 34 if top else 70 + 30 * (big - 1)
    d.rectangle([PIPE_X - pw / 2, 80, PIPE_X + pw / 2, 220], fill=(150, 156, 168, 255), outline=ink, width=4)
    d.rectangle([PIPE_X - pw / 2 - 14, 74, PIPE_X + pw / 2 + 14, 96], fill=(120, 126, 138, 255), outline=ink, width=4)
    d.rectangle([PIPE_X - pw / 2 - 10, 200, PIPE_X + pw / 2 + 10, 240], fill=(170, 176, 188, 255), outline=ink, width=4)
    # the pay tag
    tag = "$3K/MO" if top else ("$5K/MO" if t < T_RAISE else "$9K/MO")
    f = font(BOLD, 34)
    tw = f.getlength(tag)
    x = PIPE_X + pw / 2 + 24
    d.rounded_rectangle([x, 130, x + tw + 28, 182], 10, fill=(18, 20, 28, 255), outline=GOLD + (255,), width=3)
    d.text((x + 14, 138), tag, font=f, fill=GOLD + (255,))
    if not top and T_RAISE <= t < T_RAISE + 1.0:
        k = 1 - prog(t, T_RAISE, T_RAISE + 1.0)
        spaced(d, x + tw / 2 + 14, 84 - 20 * (1 - k), "RAISE!", font(BOLD, 34), (120, 230, 150, int(255 * k)), 3)


def coin_stream(d, t, top):
    """Coins falling from the pipe mouth (y 240) to the surface in the bucket."""
    cx, ty, tw, h = BK
    surf = ty + h - h * level(t, top)
    n = 4 if top else (14 if t < T_RAISE else 26)
    spread = 8 if top else (26 if t < T_RAISE else 44)
    rate = 1.6 if top else 2.6
    rng = np.random.default_rng(1 if top else 2)
    for i in range(n):
        ph = (t * rate + i / n) % 1.0
        x = PIPE_X + rng.uniform(-spread, spread)
        y = lerp(240, surf, ph)
        coin(d, x, y, 9 if top else 10)


def hole_jets(d, t):
    for hx, hy, label, t_in in HOLES:
        if t < t_in:
            continue
        k_in = smooth(prog(t, t_in, t_in + 0.3))
        x0, y0 = hole_pos(hx, hy)
        sx = 1 if hx >= 0 else -1
        rng = np.random.default_rng(int(hy))
        for i in range(7):
            ph = (t * 2.2 + i / 7 + rng.uniform(0, 0.1)) % 1.0
            vx = sx * (160 + 60 * rng.uniform())
            x = x0 + vx * ph
            y = y0 + 420 * ph * ph
            if y < FYP - 4:
                coin(d, x, y, 8, int(255 * k_in))


def draw_bucket(im, d, t, top):
    ink = INK + (255,)
    cx, ty, tw, h = BK
    d.polygon(bucket_poly(), fill=(70, 74, 86, 255))
    lv = level(t, top)
    if lv > 0.01:
        d.polygon(bucket_poly(lv), fill=GOLD + (255,))
        # coin texture on the surface
        poly = bucket_poly(lv)
        y = poly[0][1]
        for j in range(9):
            x = lerp(poly[0][0] + 14, poly[1][0] - 14, j / 8)
            coin(d, x, y + 4 + 4 * (j % 2), 12)
    # bucket body outline, bands and handle
    d.line(bucket_poly() + [bucket_poly()[0]], fill=ink, width=6)
    for k in (0.3, 0.7):
        p = bucket_poly(k)
        d.line([p[0], p[1]], fill=(110, 116, 130, 255), width=4)
    d.arc([cx - tw / 2 - 10, ty - 120, cx + tw / 2 + 10, ty + 100], 200, 340, fill=(150, 156, 168, 255), width=6)
    if not top:
        for hx, hy, label, t_in in HOLES:
            if t < t_in:
                continue
            k = out_back(prog(t, t_in, t_in + 0.25))
            if k < 0.05:
                continue
            x, y = hole_pos(hx, hy)
            r = 15 * k
            d.ellipse([x - r, y - r, x + r, y + r], fill=(6, 6, 8, 255), outline=ink, width=3)
            # the tag of the hole, in a column right of the bucket, with a thin line to it
            f = font(BOLD, int(26 * min(1.0, k)) or 1)
            tw2 = f.getlength(label)
            tx = cx + tw / 2 + 24
            ty2 = y - 18
            d.line([(x + r, y), (tx, y)], fill=(220, 60, 60, 255), width=2)
            d.rounded_rectangle([tx, ty2, tx + tw2 + 18, ty2 + 36], 7, fill=(220, 60, 60, 255))
            d.text((tx + 9, ty2 + 4), label, font=f, fill=(255, 255, 255, 255))
    if top and t >= T_FULL:
        k = smooth(prog(t, T_FULL, T_FULL + 0.4))
        g = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([cx - 220, ty - 120, cx + 220, ty + h + 60], fill=GOLD + (int(70 * k),))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(50)))


def floor_coins(d, t):
    """What leaked: a scatter on the floor that keeps vanishing (spent)."""
    rng = np.random.default_rng(5)
    for i in range(18):
        x = BK[0] + rng.choice([-1, 1]) * rng.uniform(200, 380)
        life = (t * 0.9 + i / 18) % 1.0
        a = int(255 * (1 - life))
        coin(d, x, FYP - 6, 9, a)


def big_number(im, t, top):
    if t < T_FULL:
        return
    k = out_back(prog(t, T_FULL, T_FULL + 0.35))
    s = "SAVED $36,000" if top else "SAVED $0"
    col = (120, 230, 150) if top else (255, 90, 80)
    f = font(BOLD, 64)
    tw = f.getlength(s) + 4 * len(s)
    lay = Image.new("RGBA", (int(tw + 60), 110), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, lay.width - 1, 109], 16, fill=(10, 10, 14, 235), outline=col + (255,), width=4)
    spaced(ld, lay.width / 2, 18, s, f, col + (255,), 4)
    lay = lay.resize((max(1, int(lay.width * k)), max(1, int(110 * k))), Image.LANCZOS)
    im.alpha_composite(lay, (int(BK[0] - lay.width / 2), int(BK[1] + BK[3] / 2 - lay.height / 2)))


def sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    return cv.done()


BG = None
FRAME0 = None


def panel(t, top):
    im = BG.copy()
    d = ImageDraw.Draw(im)
    draw_pipe(d, t, top)
    if not top:
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        floor_coins(ImageDraw.Draw(lay), t)
        im.alpha_composite(lay)
        d = ImageDraw.Draw(im)
    draw_bucket(im, d, t, top)
    d = ImageDraw.Draw(im)
    if not (not top and t >= T_FULL):
        coin_stream(d, t, top)
    else:
        coin_stream(d, t, top)
    if not top:
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        hole_jets(ImageDraw.Draw(lay), t)
        im.alpha_composite(lay)
        d = ImageDraw.Draw(im)
        draw_tags_again = True
    pose, hip, facing = person(t, top)
    pts = AJ.place(pose, hip, facing, SC)
    spr, off = sprite(pts, FIG, FIG_FAR, facing)
    if top:
        im.alpha_composite(PW.glow_of(spr, 0.35, 12), off)
    im.alpha_composite(spr, off)
    big_number(im, t, top)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (2, 2, 3, 255))
    img.alpha_composite(panel(t, True), (0, TOP_Y0))
    img.alpha_composite(panel(t, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    fl = font(BOLD, 42)
    if t < T_L1:
        spaced(d, W / 2, TOP_Y0 + 24, "KEEPS MORE", fl, (250, 250, 252, 255), 12)
    spaced(d, W / 2, BOT_Y0 + 24, "EARNS MORE", fl, (230, 232, 238, 255), 12)
    fm = font(BOLD, 54)
    for t0, s2, y in ((T_L1, LINE1, 40), (T_L2, LINE2, 108)):
        if t < t0:
            continue
        k = int(clamp((t - t0) * CPS, 0, len(s2)))
        full = sum(fm.getlength(c) for c in s2) + 3 * (len(s2) - 1)
        xx = W / 2 - full / 2
        for c in s2[:k]:
            d.text((xx, y), c, font=fm, fill=(250, 250, 252, 255))
            xx += fm.getlength(c) + 3
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    if t >= T_FOLLOW:
        k = smooth(prog(t, T_FOLLOW, T_FOLLOW + 0.3))
        arr *= 1 - 0.75 * k
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        ff = font(BOLD, 76)
        spaced(cd, W / 2, H / 2 - 90, "FOLLOW", ff, (250, 250, 252, int(255 * k)), 6)
        spaced(cd, W / 2, H / 2 + 6, "FOR MORE", ff, (250, 250, 252, int(255 * k)), 6)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        base.alpha_composite(card)
        return np.asarray(base.convert("RGB"))
    return np.clip(arr, 0, 255).astype(np.uint8)


def init_worker():
    global BG
    BG = build_bg()


def render(i):
    global FRAME0
    t = i / FPS
    fr = frame(t)
    if t > DUR - XFADE:
        if FRAME0 is None:
            FRAME0 = frame(0.0).astype(np.float32)
        k = smooth(prog(t, DUR - XFADE, DUR))
        fr = (fr.astype(np.float32) * (1 - k) + FRAME0 * k).astype(np.uint8)
    return fr.tobytes()


def coin_clink(seed):
    f = 2600 + (seed * 137) % 1800
    a = tone(f, 0.12, (1, 0.5, 0.3), a=0.001, d=0.05)
    b = tone(f * 1.5, 0.12, (1,), a=0.001, d=0.03)
    return a + 0.3 * b


def audio():
    n = int(DUR * SR)
    mus = music.score(MUSIC, DUR, t_end=T_FULL, t_warm=T_L1 - 0.4, t_line=T_L1, start=0.0, loud=1.2)
    fx = np.zeros((n, 2))
    # frame 0: the gush of coins below hits at once (a cascade), a soft drip above
    rng = np.random.default_rng(4)
    for tk in np.arange(0.0, T_FULL, 0.035):
        dens = 0.5 if tk < T_RAISE else 0.9
        if rng.uniform() < dens:
            mix_in(fx, coin_clink(int(tk * 1000)), tk, 0.012, 0.35)
    for tk in np.arange(0.0, T_FULL, 0.16):
        mix_in(fx, coin_clink(int(tk * 777)), tk, 0.014, -0.35)
    # a low rush under the pouring
    r = noise(T_FULL, 8, lo=300, hi=3000) * 0.012
    i1 = len(r)
    fx[:i1, 1] += r * (1 + (np.arange(i1) / SR > T_RAISE))
    # pops when new holes open
    for hx, hy, label, t_in in HOLES:
        mix_in(fx, tone(180, 0.15, (1, 0.5), a=0.002, d=0.07, sweep=90), max(0.0, t_in), 0.12, 0.3)
    mix_in(fx, tone(1046, 0.2, (1, 0.4), a=0.002, d=0.1), T_RAISE, 0.04, 0.3)
    mix_in(fx, tone(1318, 0.25, (1, 0.4), a=0.002, d=0.12), T_RAISE + 0.08, 0.04, 0.3)
    # the twist: a bright "full" chime above, an empty hollow "clunk" below
    for j, m in enumerate((84, 88, 91)):
        mix_in(fx, music.music_box(midi(m), 1.4), T_FULL + 0.06 * j, 0.05, -0.3)
    mix_in(fx, tone(110, 0.5, (1, 0.6, 0.3), a=0.003, d=0.25), T_FULL + 0.1, 0.12, 0.3)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i2, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i2 + int(t0), lo=1200, hi=4000) * env(int(0.03 * SR), 0.001, 0.008),
                       t0 + i2 / CPS, 0.05)
    x = mus + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "leaky-bucket.mp4"
    only = os.environ.get("ONLY_FRAMES")
    if only:
        init_worker()
        os.makedirs(out, exist_ok=True)
        for s in only.split(","):
            t = float(s)
            Image.fromarray(np.frombuffer(render(int(round(t * FPS))), np.uint8).reshape(H, W, 3)).save(
                os.path.join(out, f"f{t:05.2f}.png"))
        return
    wav = out + ".wav"
    write_wav(wav, audio())
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init_worker) as pool:
        for i, b in enumerate(pool.imap(render, range(NF), chunksize=4)):
            p.stdin.write(b)
            if i % 120 == 0:
                print(f"{i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)


if __name__ == "__main__":
    main()
