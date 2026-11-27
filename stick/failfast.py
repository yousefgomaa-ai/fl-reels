#!/usr/bin/env python3
"""FAIL FASTER - four scenes, one lesson. ~35 s.

1 ARCHERY    WAITING aims forever (0 shots). TRYING fires again and again - misses pile up - bullseye.  HITS 12 vs 0
2 SKATE      "SUCCESS IS 100 FALLS AWAY." ATTEMPT 1..100, every fall stays as a ghost, the sky turns day/night;
             100 at sunrise: he lands it, the ghosts fade.
3 MOUNTAIN   QUITTING vs ONE MORE STEP in a snowstorm. "I'M DONE." - he slides down to a warm cabin
             ("IT'S WARMER DOWN HERE."). The other one keeps climbing; sunrise at the summit.
4 SCULPTOR   "NOBODY STARTS FINISHED." A raw stone marked YOU. Every strike: FAILURE, REJECTION, DOUBT, LOSS, FEAR...
             fly off. Inside: a statue of him.   FAIL FASTER.

    python3 stick/failfast.py --stills [t ...]   # -> stick/failfast/stills.png
    python3 stick/failfast.py stick/failfast.mp4 [--sfx]
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
import hq  # noqa
import race as R  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import hero, face, S, GOLD, RED  # noqa
from money import text, put, track  # noqa

FPS, SR = 30, 44100
SCENES = [("archery", 0.0, 8.4), ("skate", 8.4, 17.6), ("mountain", 17.6, 26.4), ("sculptor", 26.4, 35.0)]
DUR = 35.0
NF = int(round(DUR * FPS))
STAND = PW.STAND
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
PALE = (190, 196, 210)


def scene_at(t):
    for k, a, b in SCENES:
        if a <= t < b:
            return k, t - a, b - a
    return SCENES[-1][0], t - SCENES[-1][1], SCENES[-1][2] - SCENES[-1][1]


def new():
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    return st, ImageDraw.Draw(st)


def set_arm(p, side, tgt, sgn=1):
    p = dict(p)
    p["h" + side] = tgt
    p["e" + side] = ik(p["neck"], tgt, 42 * S, 40 * S, sgn)
    return p


def plain(st, p, expr, t, f=1, body=(214, 218, 230)):
    figure(st, p, S, light=(0.4, -0.9), body=body)
    face(ImageDraw.Draw(st), p, expr, f, t)


def label(im, x, y, s, size=30, col=PALE, a=1.0):
    if a <= 0.01:
        return
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    PW.spaced(ImageDraw.Draw(g), x, y, s, font(SERIF, size), col + (int(255 * clamp(a)),), 5)
    im.alpha_composite(g)


def glow_ell(layer, x, y, rx, ry, col, scale=K):
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse(((x - rx) * scale, (y - ry) * scale, (x + rx) * scale, (y + ry) * scale), col)
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(20 * scale)))


def glow_text(im, x, y, s, size, col, a=1.0, serif=False):
    f = font(SERIF if serif else "InterDisplay-Bold.otf", size)
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    PW.spaced(ImageDraw.Draw(g), x, y, s, f, col + (int(160 * a),), 3)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))
    g2 = Image.new("RGBA", im.size, (0, 0, 0, 0))
    PW.spaced(ImageDraw.Draw(g2), x, y, s, f, col + (int(255 * a),), 3)
    im.alpha_composite(g2)


def bg(top, bot):
    """vertical gradient background as an RGBA image (1x)"""
    a = np.zeros((H, W, 3), np.float32)
    k = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    a[:] = np.array(top, np.float32) * (1 - k) + np.array(bot, np.float32) * k
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")


def finish(st, back, z=1.0, cx=W / 2, cy=H / 2):
    """stage (2x) over a 1x background, camera, light"""
    b = back.resize((W * K, H * K), Image.BILINEAR) if back.size != (W * K, H * K) else back.copy()
    b.alpha_composite(st)
    im = hq.camera(b, z, z * (W / 2 - cx) * K, z * (H / 2 - cy) * K)
    return im.resize((W, H), Image.LANCZOS)


def spot(im, cx, cy, rx=560, ry=820, floor=0.25):
    a = np.asarray(im.convert("RGB"), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
    a *= (floor + (1.05 - floor) * g)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def cone(d, x, top, bot, w0, w1, col=(255, 236, 200), a=26):
    poly(d, [(x - w0, top), (x + w0, top), (x + w1, bot), (x - w1, bot)], col + (a,))


# ================================================================ 1. ARCHERY
LANES = [("WAITING", 900), ("TRYING", 1430)]     # label, floor y
TGT_X = 830
ARROWS = []
_rng = np.random.default_rng(12)
for i in range(18):
    t0 = 0.35 + i * 0.4
    if i < 5:
        dy = _rng.choice([-1, 1]) * _rng.uniform(70, 140)      # off the target
    elif i < 17:
        dy = _rng.uniform(-50, 50) * (1 - (i - 5) / 14)        # closer and closer
    else:
        dy = 0.0
    ARROWS.append((t0, dy))
T_BULL = ARROWS[-1][0] + 0.32


def arrow(d, x, y, ang=0.0, L=90):
    c_, s_ = math.cos(ang), math.sin(ang)
    line(d, [(x - L * c_, y - L * s_), (x, y)], (210, 190, 150, 255), 4)
    poly(d, [(x + 12 * c_, y + 12 * s_), (x - 4 * s_, y + 4 * c_), (x + 4 * s_, y - 4 * c_)], (220, 220, 230, 255))
    for k in (0.85, 0.95):
        bx, by = x - L * k * c_, y - L * k * s_
        line(d, [(bx, by), (bx - 10 * c_ - 8 * s_, by - 10 * s_ + 8 * c_)], (230, 70, 60, 255), 3)


def target(d, x, y, flash=0.0):
    for r, col in ((80, (240, 240, 240)), (64, (40, 40, 44)), (48, (60, 110, 220)), (32, (220, 60, 50)), (16, (250, 210, 60))):
        ell(d, x, y, r * 0.45, r, col + (255,))
    line(d, [(x + 10, y + 80), (x + 30, y + 190)], (110, 80, 50, 255), 6)
    if flash > 0:
        glow_ell(d._image, x, y, 40 + 120 * flash, 60 + 160 * flash, (255, 230, 140, int(160 * (1 - flash))))


def archer(st, d, x, fl, t, mode):
    bow_x = x + 70
    if mode == "wait":
        shake = 3 * math.sin(t * 40)
        p = place(dict(STAND, el=(40, -110), hl=(78 + shake, -112), er=(10, -112), hr=(-20, -110)), (x, fl - 113 * S), 1, S)
        expr = "nervous" if t < 6.5 else "sad"
        if t > 7.0:   # gives up, lowers the bow
            p = place(dict(STAND, head=(10, -140)), (x, fl - 113 * S), 1, S)
    else:
        ph = min((t - 0.35) % 0.4 / 0.4, 1.0) if t >= 0.35 and t < T_BULL else 1.0
        draw = smooth(clamp(ph / 0.7))
        p = place(dict(STAND, el=(40, -110), hl=(78, -112), er=(lerp(40, 10, draw), -112), hr=(lerp(60, -20, draw), -110)),
                  (x, fl - 113 * S), 1, S)
        expr = "happy" if t >= T_BULL + 0.2 else "determined"
    hx, hy = p["hl"]
    d.arc(((hx - 30) * K, (hy - 90) * K, (hx + 30) * K, (hy + 90) * K), 270, 90, fill=(160, 110, 60, 255), width=int(5 * K))
    line(d, [(hx, hy - 88), (p["hr"][0], p["hr"][1]), (hx, hy + 88)], (230, 230, 230, 200), 2)
    if mode == "wait" and t <= 7.0:
        arrow(d, hx + 30, hy, 0.0, 100)
    if mode == "wait":
        plain(st, p, expr, t)
    else:
        hero(st, p, "plain", 1, expr, t)


def archery(u):
    st, d = new()
    back = bg((10, 12, 20), (4, 4, 8))
    bd = ImageDraw.Draw(back)
    for lab, fl in LANES:
        bd.rectangle((0, fl, W, fl + 6), (60, 62, 74))
        bd.polygon([(TGT_X - 120, 0), (TGT_X + 120, 0), (TGT_X + 220, fl), (TGT_X - 220, fl)], (22, 24, 34))
        bd.polygon([(180 - 100, 0), (180 + 100, 0), (180 + 200, fl), (180 - 200, fl)], (20, 22, 30))
    hits = 0
    for idx, (lab, fl) in enumerate(LANES):
        ty = fl - 300
        flash = smooth(prog(u, T_BULL, T_BULL + 0.5)) if idx == 1 and u >= T_BULL else 0.0
        target(d, TGT_X, ty, flash)
        archer(st, d, 290, fl, u, "wait" if idx == 0 else "try")
    # TRYING's arrows
    fl = LANES[1][1]
    ty = fl - 300
    for t0, dy in ARROWS:
        if u < t0:
            continue
        v = clamp((u - t0) / 0.3)
        x0, y0 = 410, fl - 220
        x1 = TGT_X - 6 if abs(dy) < 80 else TGT_X + 40
        y1 = ty + dy
        x = lerp(x0, x1, v)
        y = lerp(y0, y1, v) - 60 * 4 * v * (1 - v)
        if v >= 1 and abs(dy) >= 80:     # misses fall to the floor
            w = clamp((u - t0 - 0.3) / 0.3)
            x, y = x1 + 30 * w, lerp(y1, fl - 6, w * w)
        arrow(d, x, y, 0.0 if v >= 1 else -0.2 + 0.4 * v)
        if v >= 1 and abs(dy) < 80:
            hits += 1
    im = finish(st, back, 1.3, 560, 1120)
    im = spot(im, 540, 1100, 620, 900, 0.3)
    def sy_(y):
        return (y - 1120) * 1.3 + H / 2
    for lab, fl in LANES:
        label(im, 330, sy_(fl - 420), lab, 40)
    glow_text(im, 790, sy_(LANES[0][1] - 420) - 30, "0", 72, (200, 204, 214))
    col = GOLD if u >= T_BULL else (246, 246, 250)
    glow_text(im, 790, sy_(LANES[1][1] - 420) - 30, str(hits), 72, col)
    return im


# ================================================================ 2. SKATE
SKY = [((40, 90, 160), (150, 200, 240)), ((40, 30, 80), (240, 140, 90)), ((6, 8, 24), (20, 30, 60)),
       ((60, 40, 90), (250, 170, 120))]
BOX = (500, 640)          # the stair set / box to jump
T_100 = 6.2


def attempt_no(u):
    if u >= T_100:
        return 100
    if u < 1.3:
        return 1
    return min(99, int(2 + 97 * ((u - 1.3) / (T_100 - 1.3)) ** 1.8))


def sky_cols(u):
    if u >= T_100:
        return (40, 30, 80), (255, 160, 90)
    ph = (attempt_no(u) / 6.0) % len(SKY)
    i = int(ph)
    f = ph - i
    a, b = SKY[i], SKY[(i + 1) % len(SKY)]
    return tuple(int(lerp(a[0][k], b[0][k], f)) for k in range(3)), tuple(int(lerp(a[1][k], b[1][k], f)) for k in range(3))


def skater(v, success, seed=0):
    """pose + hip + board for one attempt, v 0..1"""
    rng = np.random.default_rng(seed)
    x = lerp(120, 900, v)
    gy = FLOOR
    jump = 0.0
    if 0.38 < v < 0.66:
        jump = math.sin(math.pi * (v - 0.38) / 0.28) * 190
    crouch = dict(STAND, kl=(20, 40), fl=(-6, 100), kr=(36, 46), fr=(30, 104), el=(-30, -80), hl=(-60, -60),
                  er=(30, -90), hr=(70, -80))
    board = (x, gy - 8 - jump, 0.0)
    if success or v < 0.6:
        pose = crouch if jump > 20 else dict(STAND, el=(-30, -80), hl=(-60, -70), er=(30, -80), hr=(60, -70))
        hip = (x, gy - 16 - 113 * S + (20 if jump > 20 else 0) - jump)
        if jump > 20:
            board = (x, gy - 16 - jump + 2, 0.3 * math.sin(math.pi * (v - 0.38) / 0.28 * 2))
        return pose, hip, board, 0.0
    # the fall: tumble forward
    w = clamp((v - 0.6) / 0.25)
    rot = w * (2.2 + rng.uniform(-0.3, 0.3))
    fx = lerp(x, x + 60, w)
    hip = (fx, lerp(gy - 113 * S - 40, gy - 40, w))
    pose = lerp_pose(crouch, {"head": (-150, -10), "neck": (-108, -6), "el": (-80, 30), "hl": (-46, 40), "er": (-80, -44),
                              "hr": (-40, -70), "kl": (56, -24), "fl": (113, -2), "kr": (56, -6), "fr": (113, 6)}, w)
    board = (x + 140 * w + rng.uniform(0, 60), gy - 8 - 80 * math.sin(math.pi * w), w * 6)
    return pose, hip, board, rot


def draw_board(d, x, y, rot):
    c_, s_ = math.cos(rot), math.sin(rot)
    pts = [(-46, -5), (46, -5), (50, 3), (-50, 3)]
    poly(d, [(x + px * c_ - py * s_, y + px * s_ + py * c_) for px, py in pts], (230, 70, 60, 255))
    for wx in (-30, 30):
        ell(d, x + wx * c_, y + wx * s_ + 9, 7, 7, (240, 240, 240, 255))


def skate(u):
    st, d = new()
    top, bot = sky_cols(u)
    back = bg(top, bot)
    bd = ImageDraw.Draw(back)
    if u >= T_100 - 0.2:   # the sun
        k = smooth(prog(u, T_100 - 0.2, T_100 + 0.8))
        sy = lerp(1300, 1080, k)
        glow_ell(back, 760, sy, 260, 260, (255, 190, 110, int(120 * k)), scale=1)
        bd.ellipse((760 - 90, sy - 90, 760 + 90, sy + 90), (255, 214, 140, int(255 * k)))
    for x, h in ((0, 260), (140, 330), (300, 220), (700, 300), (880, 380)):    # city silhouette
        bd.rectangle((x, FLOOR - h, x + 150, FLOOR), (14, 14, 24))
    bd.rectangle((0, FLOOR, W, H), (34, 34, 44))
    poly(d, [(BOX[0], FLOOR), (BOX[0] + 30, FLOOR - 70), (BOX[1] - 30, FLOOR - 70), (BOX[1], FLOOR)], (120, 120, 132, 255),
         outline=(70, 70, 80, 255), w=2)
    n = attempt_no(u)
    # ghosts of every fall so far
    if u < T_100 + 0.6:
        ga = 0.16 * (1 - smooth(prog(u, T_100, T_100 + 0.6)))
        gl = Image.new("RGBA", st.size, (0, 0, 0, 0))
        for k in range(1, min(n, 40)):
            pose, hip, board, rot = skater(0.6 + 0.25 * ((k * 0.37) % 1), False, seed=k)
            p = place(pose, (hip[0] + ((k * 53) % 140) - 70, hip[1]), 1, S)
            figure(gl, p, S, light=(0.4, -0.9), body=(220, 230, 255))
        a = np.asarray(gl.split()[3], np.float32) * ga
        gl.putalpha(Image.fromarray(a.astype(np.uint8)))
        st.alpha_composite(gl)
    # the current attempt
    if u < 1.3:
        v = u / 1.3
    elif u < T_100:
        per = 0.55
        v = ((u - 1.3) % per) / per
    else:
        v = clamp((u - T_100) / 2.0)
    success = u >= T_100
    pose, hip, board, rot = skater(v, success, seed=n)
    p = place(pose, hip, 1, S)
    if rot:
        p = {k: (hip[0] + (x - hip[0]) * math.cos(rot) - (y - hip[1]) * math.sin(rot),
                 hip[1] + (x - hip[0]) * math.sin(rot) + (y - hip[1]) * math.cos(rot)) for k, (x, y) in p.items()}
    draw_board(d, *board)
    hero(st, p, "plain", 1, "happy" if success and v > 0.7 else ("shocked" if rot else "determined"), u)
    im = finish(st, back, 1.75, 540, FLOOR - 190)
    im = spot(im, 540, 1050, 700, 900, 0.45)
    label(im, 540, 90, "SUCCESS IS 100 FALLS AWAY.", 32, a=1 - smooth(prog(u, 2.6, 3.0)))
    label(im, 540, 90, "FALL FASTER.", 36, col=(246, 240, 226), a=smooth(prog(u, 3.0, 3.3)) * (1 - smooth(prog(u, T_100 - 0.3, T_100))))
    label(im, 540, 170, "ATTEMPT", 22)
    glow_text(im, 540, 200, str(n), 96, GOLD if n == 100 else (246, 246, 250))
    return im


# ================================================================ 3. MOUNTAIN
T_QUIT, T_TOP = 2.6, 7.0


def slope_pt(s, side):
    """a point on the climbing line, s 0 (base) .. 1 (summit)"""
    x0 = 170 if side == 0 else 520
    return lerp(x0, 560, s), lerp(FLOOR + 600, 360, s)


def climber_pose(t):
    a = math.sin(t * 7)
    return dict(STAND, el=(20, -150 - 10 * a), hl=(40, -200 - 20 * a), er=(30, -150 + 10 * a), hr=(50, -200 + 20 * a),
                kl=(16, 50 + 10 * a), fl=(10, 110), kr=(26, 50 - 10 * a), fr=(30, 110), head=(16, -148))


def mountain(u):
    st, d = new()
    dawn = smooth(prog(u, T_TOP - 1.0, T_TOP + 0.6))
    top = tuple(int(lerp(a, b, dawn)) for a, b in zip((8, 12, 24), (60, 70, 130)))
    bot = tuple(int(lerp(a, b, dawn)) for a, b in zip((30, 38, 60), (255, 170, 110)))
    back = bg(top, bot)
    bd = ImageDraw.Draw(back)
    if dawn > 0:
        glow_ell(back, 780, 420, 260, 260, (255, 200, 120, int(130 * dawn)), scale=1)
        bd.ellipse((780 - 80, 420 - 80, 780 + 80, 420 + 80), (255, 220, 150, int(255 * dawn)))
    # the mountain
    poly(d, [(-200, H + 200), (560, 330), (1300, H + 200)], (210, 218, 232, 255))
    poly(d, [(560, 330), (1300, H + 200), (760, H + 200)], (170, 178, 196, 255))
    for side in (0, 1):
        pts = [slope_pt(s, side) for s in np.linspace(0, 1, 12)]
        line(d, pts, (180, 120, 70, 255), 4)
    # the cabin at the bottom (where quitting leads)
    cx, cy = 230, FLOOR + 520
    poly(d, [(cx - 90, cy), (cx + 90, cy), (cx + 90, cy - 90), (cx, cy - 150), (cx - 90, cy - 90)], (110, 70, 50, 255))
    rrect(d, (cx - 30, cy - 70, cx + 10, cy - 30), 4, (255, 200, 110, 255))
    # QUITTING
    if u < T_QUIT:
        s = 0.18 + 0.12 * (u / T_QUIT)
        p = place(climber_pose(u), slope_pt(s, 0), 1, S * 0.9)
        plain(st, p, "tired", u)
    else:
        w = smooth(prog(u, T_QUIT + 0.5, T_QUIT + 1.6))
        s = lerp(0.3, 0.0, w)
        x, y = slope_pt(s, 0)
        if w >= 1:
            x, y = cx + 120, cy - 60
            p = place(dict(PW.SIT, head=(10, -146)), (x, y), -1, S * 0.9)
        else:
            p = place(dict(STAND, el=(-20, -100), hl=(-50, -140), er=(30, -100), hr=(60, -140)), (x, y), 1, S * 0.9)
        plain(st, p, "sad" if w < 1 else "happy", u)
    # ONE MORE STEP
    s = min(1.0, 0.18 + 0.82 * smooth(prog(u, 0.0, T_TOP)) ** 1.2)
    gust = math.sin(u * 3.1) * 8 * (1 - dawn)
    if u < T_TOP:
        p = place(climber_pose(u + 1), (slope_pt(s, 1)[0] + gust, slope_pt(s, 1)[1]), 1, S * 0.9)
        hero(st, p, "plain", 1, "determined", u)
    else:
        p = place(dict(PW.ARMS_UP), (560, 330 - 113 * S * 0.9), 1, S * 0.9)
        hero(st, p, "plain", 1, "happy", u)
    # snowstorm
    rng = np.random.default_rng(4)
    storm = 1 - 0.85 * dawn
    for _ in range(260):
        x0, y0, sp = rng.uniform(-200, W + 200), rng.uniform(0, H + 600), rng.uniform(260, 520)
        y = (y0 + u * sp) % (H + 600) - 300
        x = x0 - u * sp * 0.6 + 40 * math.sin(u + y0)
        x = (x % (W + 400)) - 200
        ell(d, x, y, 3, 3, (240, 244, 255, int(200 * storm)))
    # camera: follows the climb up the mountain
    cyc = lerp(1500, 700, smooth(prog(u, 0.0, T_TOP)))
    if u < T_QUIT + 1.8 and u > T_QUIT:
        pass
    z = lerp(1.6, 1.25, smooth(prog(u, T_TOP - 0.5, T_TOP + 0.8)))
    im = finish(st, back, z, 540, cyc)
    im = spot(im, 540, 900, 700, 1000, 0.5)
    label(im, 300, 150, "QUITTING", 30)
    label(im, 780, 150, "ONE MORE STEP", 30)
    if T_QUIT <= u < T_QUIT + 1.2:
        R.bubble(im, u, T_QUIT, T_QUIT + 1.2, "I'M DONE.", 300, 560, size=34)
    if T_QUIT + 2.0 <= u < T_QUIT + 3.6:
        R.bubble(im, u, T_QUIT + 2.0, T_QUIT + 3.6, "IT'S WARMER DOWN HERE.", 330, 1150, size=30)
    return im


# ================================================================ 4. SCULPTOR
WORDS = ["FAILURE", "REJECTION", "DOUBT", "LOSS", "FEAR", "PAIN"]
STRIKE0, STRIKE_P = 1.4, 0.85
T_REVEAL = STRIKE0 + STRIKE_P * len(WORDS)
SX, SY = 640, FLOOR - 120          # statue base


def chunks():
    rng = np.random.default_rng(21)
    out = []
    for j in range(36):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(40, 150)
        cx = SX + r * math.cos(a) * 0.9
        cy = SY - 250 + r * math.sin(a) * 1.6
        pts = []
        for k in range(7):
            aa = k / 7 * 2 * math.pi
            rr = rng.uniform(40, 75)
            pts.append((rr * math.cos(aa), rr * math.sin(aa)))
        out.append((cx, cy, pts, j % len(WORDS)))
    return out


CHUNKS = chunks()


def sculptor(u):
    st, d = new()
    back = bg((20, 16, 14), (8, 6, 6))
    bd = ImageDraw.Draw(back)
    for row in range(14):    # brick wall
        for col in range(9):
            x = col * 130 + (65 if row % 2 else 0) - 40
            y = 300 + row * 70
            bd.rectangle((x, y, x + 124, y + 64), (34 + (row * 7 + col * 3) % 10, 26, 24))
    poly(d, [(SX - 140, SY), (SX + 140, SY), (SX + 120, FLOOR), (SX - 120, FLOOR)], (90, 80, 72, 255))
    # the statue (revealed underneath)
    sp = place(dict(PW.ARMS_UP), (SX, SY - 113 * S * 1.5), 1, S * 1.5)
    figure(st, sp, S * 1.5, light=(0.4, -0.9), body=(200, 192, 176))
    nx, ny = sp["neck"]
    ell(d, nx, ny + 2, 30, 16, (176, 160, 140, 255))
    if u >= T_REVEAL:
        k = smooth(prog(u, T_REVEAL, T_REVEAL + 0.6))
        glow_ell(st, SX, SY - 200, 200, 300, (255, 220, 150, int(110 * k)))
    # the stone still around it: chunks leave strike by strike
    struck = int(max(0, (u - STRIKE0) / STRIKE_P) + 1) if u >= STRIKE0 else 0
    for j, (cx, cy, pts, wi) in enumerate(CHUNKS):
        gone_at = STRIKE0 + STRIKE_P * (j % len(WORDS)) + 0.12
        if u >= gone_at + 0.8:
            continue
        if u >= gone_at:   # flying off
            v = u - gone_at
            dx = (cx - SX) * 3.5 * v + (120 if cx > SX else -120) * v
            dy = -260 * v + 900 * v * v
            rot = v * 4
            pts2 = [(cx + dx + x * math.cos(rot) - y * math.sin(rot), cy + dy + x * math.sin(rot) + y * math.cos(rot)) for x, y in pts]
            poly(d, pts2, (128, 122, 116, 255), outline=(80, 76, 72, 255), w=2)
        else:
            poly(d, [(cx + x, cy + y) for x, y in pts], (128, 122, 116, 255), outline=(80, 76, 72, 255), w=2)
    if u < STRIKE0 + 0.3:
        PW.spaced(d, SX * K, (SY - 260) * K, "YOU", font(SERIF, 54 * K), (70, 66, 62, 255), 6)
    # him with hammer and chisel
    if u < T_REVEAL:
        ph = ((u - STRIKE0) % STRIKE_P) / STRIKE_P if u >= STRIKE0 else 0.0
        lift = math.cos(math.pi * min(1, ph / 0.2)) if ph < 0.2 else math.sin(math.pi * clamp((ph - 0.2) / 0.8))
        p = place(STAND, (380, FLOOR - 113 * S), 1, S)
        p = set_arm(p, "l", (500, FLOOR - 330), 1)
        p = set_arm(p, "r", (lerp(470, 440, lift), lerp(FLOOR - 330, FLOOR - 460, lift)), 1)
        hero(st, p, "plain", 1, "determined", u)
        line(d, [(500, FLOOR - 330), (540, FLOOR - 330)], (190, 190, 200, 255), 5)
        hx_, hy_ = p["hr"]
        line(d, [(hx_, hy_), (hx_ + 10, hy_ - 50)], (130, 90, 50, 255), 6)
        rrect(d, (hx_ - 6, hy_ - 66, hx_ + 30, hy_ - 44), 3, (90, 92, 100, 255))
    else:
        p = place(dict(STAND, head=(20, -154)), (380, FLOOR - 113 * S), 1, S)
        hero(st, p, "plain", 1, "happy", u)
    # sparks + dust on every strike
    rng = np.random.default_rng(int(u * 30))
    for j, w in enumerate(WORDS):
        ts = STRIKE0 + STRIKE_P * j + 0.12
        if ts <= u < ts + 0.4:
            v = (u - ts) / 0.4
            for _ in range(18):
                a = rng.uniform(-2.6, -0.4)
                r = 200 * v * rng.uniform(0.5, 1.0)
                ell(d, 545 + r * math.cos(a), FLOOR - 330 + r * math.sin(a), 3, 3, (255, 200, 100, int(255 * (1 - v))))
    im = finish(st, back, 1.35, 560, FLOOR - 360)
    im = spot(im, 560, 1000, 560, 760, 0.18)
    label(im, 540, 140, "NOBODY STARTS FINISHED.", 36, col=(236, 228, 210), a=1 - smooth(prog(u, STRIKE0 - 0.2, STRIKE0 + 0.2)))
    for j, w in enumerate(WORDS):
        ts = STRIKE0 + STRIKE_P * j + 0.12
        if ts <= u < ts + STRIKE_P:
            a = hq.pop(u, ts, 0.15) * (1 - smooth(prog(u, ts + STRIKE_P - 0.2, ts + STRIKE_P)))
            glow_text(im, 540, 150, w, 60, (236, 228, 210), a=min(1, a), serif=True)
    if u >= T_REVEAL + 0.4:
        a = smooth(prog(u, T_REVEAL + 0.4, T_REVEAL + 0.8))
        glow_text(im, 540, 150, "FAIL FASTER.", 96, GOLD, a=a, serif=True)
    return im


# ================================================================ frame
FN = {"archery": archery, "skate": skate, "mountain": mountain, "sculptor": sculptor}


def whip(im, amt):
    if amt <= 0.01:
        return im
    a = np.asarray(im.convert("RGB"), np.float32)
    acc = np.zeros_like(a)
    for k in range(8):
        acc += np.roll(a, int((k - 4) * 20 * amt), axis=1)
    return Image.fromarray((acc / 8).astype(np.uint8)).convert("RGBA")


def frame(t):
    kind, u, dur = scene_at(t)
    im = FN[kind](u)
    for k, a, b in SCENES[1:]:
        if abs(t - a) < 0.14:
            im = whip(im, 1 - abs(t - a) / 0.14)
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


MUSIC = "Crossing the Chasm.mp3"


def audio(sfx_only=False):
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    if not sfx_only:
        put(out, track(MUSIC, 0.0, DUR), 0.0, 1.5, fin=0.05, fout=1.0)
    sfx = np.zeros((n, 2))
    # archery
    for t0, dy in ARROWS:
        mix_in(sfx, tone(180, 0.15, (1, 2.4), a=0.001, d=0.1), t0, 0.25, -0.3)                      # string
        mix_in(sfx, noise(0.12, 3, lo=80, hi=1500)[:int(0.12 * SR)] * env(int(0.12 * SR), 0.001, 0.08), t0 + 0.3,
               0.35 if abs(dy) < 80 else 0.15, 0.3)                                                    # thunk
    mix_in(sfx, tone(880, 0.8, (1, 2, 3), a=0.002, d=0.7), T_BULL, 0.25, 0.3)
    # skate: falls
    s0 = SCENES[1][1]
    k = 0
    while True:
        at = s0 + 1.3 * 0.62 if k == 0 else s0 + 1.3 + (k - 1) * 0.55 + 0.55 * 0.62
        if at >= s0 + T_100:
            break
        mix_in(sfx, noise(0.18, 4 + k, lo=60, hi=1200)[:int(0.18 * SR)] * env(int(0.18 * SR), 0.002, 0.12), at, 0.3, 0.0)
        k += 1
    mix_in(sfx, noise(0.25, 7, lo=100, hi=2000)[:int(0.25 * SR)] * env(int(0.25 * SR), 0.002, 0.2), s0 + T_100 + 1.32, 0.4, 0.0)
    # mountain: wind
    m0, m1 = SCENES[2][1], SCENES[2][2]
    wind = noise(m1 - m0, 11, lo=200, hi=1800)
    i0 = int(m0 * SR)
    sfx[i0:i0 + len(wind)] += (wind[: n - i0] * 0.12)[:, None]
    # sculptor: chisel strikes + stone
    c0 = SCENES[3][1]
    for j in range(len(WORDS)):
        at = c0 + STRIKE0 + STRIKE_P * j + 0.12
        mix_in(sfx, tone(1500, 0.3, (1, 2.7, 5.1), a=0.001, d=0.25), at, 0.35, -0.2)
        mix_in(sfx, noise(0.5, 20 + j, lo=80, hi=2500)[:int(0.5 * SR)] * env(int(0.5 * SR), 0.002, 0.4), at + 0.02, 0.4, 0.1)
    mix_in(sfx, tone(55, 1.0, (1, 2), a=0.002, d=0.9), c0 + T_REVEAL, 0.6, 0.0)
    for k_, a, b in SCENES[1:]:
        mix_in(sfx, noise(0.3, 9, lo=500, hi=7000)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.15, 0.1), a - 0.15, 0.2, 0.0)
    out += sfx
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.8, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [1.0, 4.5, 7.8, 9.5, 12.5, 15.2, 16.8, 19.0, 21.0, 24.8, 28.5, 33.6]
        sheet = Image.new("RGB", (300 * len(ts), 534))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((300, 534), Image.LANCZOS), (j * 300, 0))
        p = os.path.join(here, "failfast", "stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1]
    wav = out + ".wav"
    write_wav(wav, audio("--sfx" in sys.argv))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-13:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for b in pool.imap(render, range(NF), chunksize=2):
            p.stdin.write(b)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)
    print(f'Credit: Music: "{MUSIC[:-4]}" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
