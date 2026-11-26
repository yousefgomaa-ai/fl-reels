#!/usr/bin/env python3
"""THE BRICKS - Victim vs Fighter vs Builder. ~22 s.

HOOK (0-1.8): laughing faces cut fast -> a brick flies at the camera and CRACKS THE SCREEN -> close on him, a brick
"LOSER" in slow motion, he catches it an inch from his face.  "THEY'LL THROW BRICKS."
A crowd throws labelled bricks at three people. THE VICTIM covers his head and gets buried. THE FIGHTER throws them back,
starts a war, ends up hurt. THE BUILDER catches every one and builds. Re-hook: "THEY THREW HARDER." - a storm of
bricks - he catches them all. Dawn: a castle. He stands on the highest tower; the crowd below looks up.
THEY THREW BRICKS. / HE BUILT A CASTLE.

    python3 stick/bricks.py --stills [t ...]   # -> stick/bricks/stills.png
    python3 stick/bricks.py stick/bricks.mp4
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
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import hero, face, outfit, scarf, S, GOLD, RED  # noqa
from money import text, compose, put, track  # noqa

FPS, SR = 30, 44100
HOOK, DUR = 1.8, 21.0
NF = int(round(DUR * FPS))
STAND = PW.STAND
CROWD = [70, 150, 230]
CS, CA, CA2, CY = 0.6, 150, 95, FLOOR - 60     # the crowd: far away, smaller
VX, FX, BX = 360, 570, 830
BRICK = (176, 84, 58)
BRICK_D = (70, 34, 24)
CREAM = (236, 226, 200)
ORANGE = (240, 130, 40)
VBODY = (178, 188, 206)
GREY = (150, 154, 166)
WORDS = ["LOSER", "YOU CAN'T", "FAILED", "WEIRD", "GIVE UP", "NOBODY", "TOO LATE", "QUIT", "JOKE", "NOT ENOUGH"]
T_V, T_F, T_B, T_RH, T_END, T_LINES = 4.5, 7.5, 10.5, 13.6, 18.4, 19.4
BW, BH = 30, 15            # castle bricks


def growth(t):
    return smooth(prog(t, T_B + 0.2, T_END))


# ---------------------------------------------------------------- bricks
def tbrick(d, x, y, word, rot=0.0, sc=1.0):
    """a thrown brick with a word on it, centre x, y"""
    sc *= 1.7
    w, h = 74 * sc, 32 * sc
    c_, s_ = math.cos(rot), math.sin(rot)
    P = lambda px, py: (x + px * c_ - py * s_, y + px * s_ + py * c_)  # noqa
    poly(d, [P(-w / 2, -h / 2), P(w / 2, -h / 2), P(w / 2, h / 2), P(-w / 2, h / 2)], BRICK + (255,), outline=BRICK_D + (255,),
         w=2 * sc)
    if word:
        fs = int(min(17 * sc, 1.25 * w / max(4, len(word))) * K)
        tmp = Image.new("RGBA", (int(w * K), int(h * K)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.text((w * K / 2, h * K / 2), word, font=font("InterDisplay-Bold.otf", fs), fill=(255, 255, 255, 255), anchor="mm",
                stroke_width=int(2 * sc * K / 2), stroke_fill=(40, 16, 10, 255))
        tmp = tmp.rotate(-math.degrees(rot), resample=Image.BICUBIC, expand=True)
        d._image.alpha_composite(tmp, (int(x * K - tmp.size[0] / 2), int(y * K - tmp.size[1] / 2)))


def flight(t, t0, dur, a, b, arc=160):
    u = clamp((t - t0) / dur)
    return lerp(a[0], b[0], u), lerp(a[1], b[1], u) - arc * 4 * u * (1 - u), u


def throws():
    """(t0, dur, target, word) - every brick the crowd throws"""
    out = []
    rng = np.random.default_rng(4)
    j = 0
    for t0 in np.arange(1.9, T_END - 0.6, 0.22):
        tgt = ("v" if t0 < T_V + 2 else "f") if t0 < T_B else "b"
        if t0 < T_F:
            tgt = ["v", "f", "b"][j % 3]
        out.append((float(t0), 0.55, tgt, WORDS[j % len(WORDS)]))
        j += 1
    for k in range(12):   # the storm
        out.append((T_RH + 0.05 * k, 0.5, "b", WORDS[(k * 3) % len(WORDS)]))
    return out


THROWS = throws()


def n_thrown(t):
    return sum(1 for t0, d_, tg, w in THROWS if t >= t0 + d_)


# ---------------------------------------------------------------- the castle
def castle(d, g, cx=800):
    """g 0..1 growth. returns (keep_top_y, flag?)"""
    if g <= 0:
        return FLOOR

    def block(x0, x1, h, cren=True):
        if h <= 2:
            return
        rows = int(h / BH)
        for r in range(rows):
            y = FLOOR - (r + 1) * BH
            off = BW / 2 if r % 2 else 0
            x = x0 - off
            while x < x1:
                xa, xb = max(x, x0), min(x + BW, x1)
                if xb - xa > 3:
                    sh = 0.86 + 0.18 * (((int(x) * 7 + r * 13) % 10) / 10)
                    rrect(d, (xa + 0.5, y + 0.5, xb - 0.5, y + BH - 0.5), 1.5, tuple(int(c * sh) for c in BRICK) + (255,),
                          outline=BRICK_D + (255,), w=1)
                x += BW
        top = FLOOR - rows * BH
        if cren and rows > 3:
            for x in np.arange(x0, x1 - 1, BW * 1.2):
                rrect(d, (x, top - BH * 1.2, min(x + BW * 0.6, x1), top), 1.5, BRICK + (255,), outline=BRICK_D + (255,), w=1)
        return top
    wall_h = 230 * smooth(clamp(g / 0.45))
    tow_h = 400 * smooth(clamp((g - 0.15) / 0.6))
    keep_h = 600 * smooth(clamp((g - 0.05) / 0.95))
    block(cx - 210, cx - 120, tow_h)
    block(cx + 120, cx + 210, tow_h)
    block(cx - 120, cx + 120, wall_h)
    kt = block(cx - 60, cx + 60, keep_h) or FLOOR
    # gate + windows
    if wall_h > 120:
        d.chord(((cx - 40) * K, (FLOOR - 110) * K, (cx + 40) * K, (FLOOR - 30) * K), 180, 360, fill=(20, 14, 12, 255))
        rrect(d, (cx - 40, FLOOR - 70, cx + 40, FLOOR), 2, (20, 14, 12, 255))
    for x, hh in ((cx - 165, tow_h), (cx + 165, tow_h), (cx, keep_h)):
        for k in range(1, int(hh / 120)):
            rrect(d, (x - 8, FLOOR - k * 120 - 30, x + 8, FLOOR - k * 120), 6, (250, 214, 130, 255))
    return kt if keep_h > 2 else FLOOR


# ---------------------------------------------------------------- people
HOODIE = (58, 92, 160)
TANK = (232, 118, 36)
WORK = (78, 84, 98)
HAT = (246, 196, 40)


def draw_victim(st, p, expr, t, f=1):
    d0 = ImageDraw.Draw(st)
    hx, hy = p["head"]
    ell(d0, hx - f * 4, hy + 2, 36, 36, tuple(int(c * 0.8) for c in HOODIE) + (255,))     # hood
    figure(st, p, S, light=(0.4, -0.9), body=VBODY)
    d = ImageDraw.Draw(st)
    outfit(d, p, HOODIE, f, legs=True)
    face(d, p, expr, f, t)


def draw_fighter(st, p, expr, t, f=1):
    figure(st, p, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(st)
    outfit(d, p, TANK, f, legs=False)
    for side in ("l", "r"):
        line(d, [p["hip"], p["k" + side]], (30, 30, 34, 255), 26 * S)      # black shorts
    hx, hy = p["head"]
    line(d, [(hx - 30, hy - 12), (hx + 30, hy - 14)], (220, 40, 40, 255), 8)
    line(d, [(hx - f * 28, hy - 12), (hx - f * 48, hy + 8)], (220, 40, 40, 255), 6)
    face(d, p, expr, f, t)
    for side in ("hl", "hr"):
        ell(d, *p[side], 17, 15, (210, 40, 40, 255))


def draw_builder(st, p, expr, t, f=1):
    figure(st, p, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(st)
    outfit(d, p, WORK, f, legs=True)
    face(d, p, expr, f, t)
    scarf(d, p, f)
    hx, hy = p["head"]
    d.chord(((hx - 33) * K, (hy - 38) * K, (hx + 33) * K, (hy + 14) * K), 180, 360, fill=HAT + (255,))
    line(d, [(hx - 40, hy - 12), (hx + 40, hy - 12)], tuple(int(c * 0.8) for c in HAT) + (255,), 6)


def crowd_fig(st, x, t, expr, j, f=1, hit=False):
    arm = math.sin(t * 9 + j * 1.7)
    pose = dict(STAND, er=(30, -150), hr=(50 + 20 * arm, -200 + 30 * arm)) if expr == "laugh" else dict(STAND)
    if expr == "shocked":
        pose = dict(STAND, head=(4, -154), er=(26, -110), hr=(30, -150))
    if hit:
        pose = dict(STAND, head=(-24, -140), neck=(-10, -104), el=(-30, -120), hl=(-20, -160))
    p = place(pose, (x, FLOOR - 113 * S), f, S)
    figure(st, p, S, light=(0.4, -0.9), body=GREY)
    face(ImageDraw.Draw(st), p, "sad" if hit else expr, f, t)
    return p


def crowd_pt(x, y):
    return CA2 + (x - CA) * CS, CY + (y - FLOOR) * CS


def world(t, crowd_scale=CS):
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    g = growth(t)
    kt = castle(d, g, cx=BX)
    # crowd (far back, smaller)
    hit = 8.4 <= t < 9.6
    cexpr = "laugh" if t < T_END + 0.4 else "shocked"
    cl = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    for j, x in enumerate(CROWD):
        crowd_fig(cl, x, t, cexpr, j, 1, hit=(hit and j == 2))
    if crowd_scale < 0.999:
        cl = cl.resize((int(W * K * crowd_scale), int(H * K * crowd_scale)), Image.LANCZOS)
        st.alpha_composite(cl, (int(CA2 * K - CA * K * crowd_scale), int(CY * K - FLOOR * K * crowd_scale)))
    else:
        st.alpha_composite(cl)
    # victim: covers his head, buried
    pile = 190 * smooth(prog(t, 2.0, 7.4))
    vk = smooth(prog(t, 2.2, 2.8))
    vpose = lerp_pose(STAND, dict(STAND, head=(20, -120), neck=(14, -90), el=(40, -120), hl=(10, -150), er=(46, -116),
                                  hr=(16, -146), kl=(30, 20), fl=(-10, 60), kr=(-20, 54), fr=(-60, 60)), vk)
    vp = place(vpose, (VX, lerp(FLOOR - 113 * S, FLOOR - 62 * S, vk)), 1, S)
    draw_victim(st, vp, "cry" if t > 2.6 else "sad", t)
    rng = np.random.default_rng(7)
    rows = int(pile / 15)
    for r in range(rows):
        wdt = 150 - r * 6
        for k in range(int(wdt / 30) + 1):
            x = VX - wdt / 2 + k * 30 + (15 if r % 2 else 0) + rng.uniform(-4, 4)
            rrect(d, (x, FLOOR - (r + 1) * 15, x + 28, FLOOR - r * 15 - 1), 1.5, BRICK + (255,), outline=BRICK_D + (255,), w=1)
    # fighter: throws them back, ends up hurt
    tired = smooth(prog(t, 10.0, 11.0))
    thr = max([math.sin(math.pi * clamp((t - tb) / 0.35)) for tb in (7.8, 8.4, 9.0, 9.6)] + [0])
    fpose = dict(STAND, er=(10 + 40 * thr, -150 - 30 * thr), hr=(-20 + 100 * thr, -200 + 40 * thr))
    if tired > 0:
        fpose = lerp_pose(fpose, dict(STAND, head=(16, -112), neck=(10, -80), el=(30, -40), hl=(40, 0), er=(36, -36),
                                      hr=(46, 4), kl=(50, 10), fl=(100, 20), kr=(46, 14), fr=(96, 24)), tired)
    fp = place(fpose, (FX, lerp(FLOOR - 113 * S, FLOOR - 50 * S, tired)), -1, S)
    draw_fighter(st, fp, "angry" if tired < 0.5 else "tired", t, -1)
    hx, hy = fp["head"]
    if t > 9.4:   # bandage
        line(d, [(hx - 20, hy + 2), (hx + 6, hy - 22)], (240, 240, 240, 255), 6)
    # builder: on top of whatever he has built
    by = kt if kt < FLOOR else FLOOR
    catching = any(t0 + d_ - 0.1 <= t < t0 + d_ + 0.15 for t0, d_, tg, w in THROWS if tg == "b")
    if t >= T_END:
        bpose = dict(PW.ARMS_UP) if T_END + 0.3 <= t < T_END + 1.4 else dict(STAND)
        bexpr = "happy"
    else:
        bpose = dict(STAND, el=(-30, -120), hl=(-60, -150), er=(-20, -126), hr=(-50, -160)) if catching else dict(STAND)
        bexpr = "determined"
    bp = place(bpose, (BX, by - 113 * S), -1, S)
    draw_builder(st, bp, bexpr, t, -1)
    if t >= T_END + 0.2:   # the flag
        fx_, fy_ = BX + 30, by
        line(d, [(fx_, fy_), (fx_, fy_ - 150)], (60, 60, 70, 255), 4)
        wv = math.sin(t * 6)
        poly(d, [(fx_, fy_ - 150), (fx_ + 70, fy_ - 140 + 6 * wv), (fx_, fy_ - 116)], RED + (255,))
    # bricks in the air
    for t0, d_, tg, w in THROWS:
        if t0 <= t < t0 + d_:
            src = crowd_pt(CROWD[int(t0 * 10) % 3] + 40, FLOOR - 200)
            tx = {"v": (VX, FLOOR - 140), "f": (FX - 20, FLOOR - 190), "b": (BX - 30, by - 160)}[tg]
            x, y, u = flight(t, t0, d_, src, tx, arc=120 if tg != "b" else 200)
            tbrick(d, x, y, w, rot=0.25 * math.sin(u * 3 + t0))
    # bricks the fighter throws back
    for tb in (7.8, 8.4, 9.0, 9.6):
        if tb + 0.15 <= t < tb + 0.6:
            x, y, u = flight(t, tb + 0.15, 0.45, (FX - 40, FLOOR - 230), crowd_pt(CROWD[2], FLOOR - 160), arc=60)
            tbrick(d, x, y, "", rot=0.3 * math.sin(u * 4))
    return st


# ---------------------------------------------------------------- background
_B = {}


def background(t):
    if "sk" not in _B:
        img = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(3)
        x = 0
        while x < W:
            w = rng.uniform(60, 130)
            h = rng.uniform(160, 420)
            poly(d, [(x, FLOOR - h), (x + w, FLOOR - h), (x + w, FLOOR), (x, FLOOR)], (16, 18, 26, 255))
            for yy in np.arange(FLOOR - h + 14, FLOOR - 10, 22):
                for xx in np.arange(x + 8, x + w - 8, 16):
                    if rng.uniform() < 0.15:
                        rrect(d, (xx, yy, xx + 7, yy + 10), 1, (230, 190, 110, 140))
            x += w + rng.uniform(4, 20)
        _B["sk"] = img
    dw = smooth(prog(t, T_END - 1.0, T_LINES + 1.0))
    img = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    if dw > 0:
        d = ImageDraw.Draw(img)
        for j in range(34):
            k = j / 33
            d.rectangle((0, j * 40 * K, W * K, (j + 1) * 40 * K),
                        (int(lerp(30, 255, k)), int(lerp(30, 150, k)), int(lerp(70, 90, k)), int(255 * dw * (0.2 + 0.8 * k))))
        sy = lerp(1300, 860, dw)
        for r, a in ((260, 40), (170, 80), (95, 255)):
            d.ellipse(((300 - r) * K, (sy - r) * K, (300 + r) * K, (sy + r) * K), (255, 214, 130, int(a * dw)))
    img.alpha_composite(_B["sk"])
    return img


def crack(im, t, t0):
    """the screen breaks"""
    u = t - t0
    if u < 0:
        return im
    d = ImageDraw.Draw(im)
    cx, cy = 420, 760
    rng = np.random.default_rng(11)
    grow = smooth(clamp(u / 0.08))
    for j in range(14):
        a = j / 14 * 2 * math.pi + rng.uniform(-0.2, 0.2)
        pts = [(cx, cy)]
        r = 0
        while r < 900 * grow:
            r += rng.uniform(40, 110)
            a += rng.uniform(-0.25, 0.25)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.line(pts, (20, 20, 24, 200), 5)
        d.line(pts, (240, 244, 255, 230), 2)
    for rr in (60, 130, 220):
        if rr < 900 * grow:
            d.ellipse((cx - rr, cy - rr * 0.9, cx + rr, cy + rr * 0.9), outline=(240, 244, 255, 150), width=2)
    return im


# ---------------------------------------------------------------- frame
SPOTS = ((340, 0.8), (800, 1.0))


def shot(t):
    """a moving camera for the story"""
    if t < T_V:      # pan from the crowd to the three
        k = smooth(prog(t, HOOK, T_V))
        return lerp(1.7, 1.3, k), lerp(240, 600, k), lerp(1170, 1150, k)
    if t < T_F:      # push in on the victim
        k = smooth(prog(t, T_V, T_F))
        return lerp(1.8, 2.3, k), VX, lerp(1190, 1215, k)
    if t < T_B:      # the fighter, whip toward the crowd when he throws
        k = smooth(prog(t, 7.9, 8.5)) * (1 - smooth(prog(t, 9.4, 10.0)))
        return lerp(1.9, 1.5, k), lerp(FX, 330, k), 1190
    if t < T_END:    # crane up with the castle
        g = growth(t)
        return lerp(1.7, 1.15, g), lerp(BX - 30, BX - 120, g), lerp(1190, 960, g)
    k = smooth(prog(t, T_END, T_LINES))
    return lerp(1.15, 1.0, k), lerp(BX - 120, 540, k), lerp(960, 960, k)


def frame(t):
    if t < HOOK:
        if t < 0.5:   # laughing faces, fast cuts
            j = min(2, int(t / 0.17))
            st = world(2.4 + t, crowd_scale=1.0)
            im = compose(st, None, 4.2, CROWD[j] + 10, FLOOR - 250, spots=SPOTS, back=background(2.4 + t), refl=False)
        elif t < 0.9:  # a brick flies at the lens and cracks it
            st = world(2.4 + t)
            im = compose(st, None, 1.3, 520, 1150, spots=SPOTS, back=background(3.0), refl=False)
            u = smooth(clamp((t - 0.5) / 0.3))
            lay = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
            tbrick(ImageDraw.Draw(lay), lerp(300, 420, u), lerp(1300, 760, u), "LOSER", rot=0.25 * u, sc=lerp(0.6, 5.0, u ** 2))
            im.alpha_composite(lay.resize((W, H), Image.LANCZOS))
            im = crack(im, t, 0.8)
        else:          # close on him: catches LOSER an inch from his face
            u = clamp((t - 0.9) / 0.5)
            st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
            d = ImageDraw.Draw(st)
            k = smooth(clamp((u - 0.55) / 0.35))
            pose = dict(STAND, er=(lerp(10, -40, k), lerp(-58, -130, k)), hr=(lerp(14, -70, k), lerp(-10, -150, k)))
            p = place(pose, (BX, FLOOR - 113 * S), -1, S)
            draw_builder(st, p, "determined", t, -1)
            hx, hy = p["head"]
            stop = hx - 110
            bx = lerp(BX - 460, stop, min(1, u / 0.9))
            p = dict(p)
            tgt = (lerp(p["hr"][0], stop + 30, k), lerp(p["hr"][1], hy + 6, k))
            p["hr"] = tgt
            p["er"] = ik(p["neck"], tgt, 42 * S, 40 * S, 1)
            st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
            d = ImageDraw.Draw(st)
            draw_builder(st, p, "determined", t, -1)
            tbrick(d, bx - 10, hy + 6, "LOSER", rot=0.1, sc=0.9)
            im = compose(st, None, 3.6, BX - 40, hy + 20, spots=SPOTS, back=background(3.0), refl=False)
            im = crack(im, t, 0.8)
        a = hq.pop(t, 0.85, 0.2) if t >= 0.85 else 0
        if a > 0:
            text(im, W / 2, 1460, "THEY'LL THROW", int(96 * max(0.3, a)))
            text(im, W / 2, 1460 + int(108 * max(0.3, a)), "BRICKS.", int(96 * max(0.3, a)), col=GOLD)
        if t < 0.06 or 0.8 <= t < 0.84:
            im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), 0.35).convert("RGBA")
        return np.asarray(im.convert("RGB"))
    st = world(t)
    z, cx, cy = shot(t)
    im = compose(st, None, z, cx, cy, spots=SPOTS, back=background(t), refl=True)
    d = ImageDraw.Draw(im)
    if t < T_END + 0.4:
        PW.spaced(d, W / 2, 40, "BRICKS THROWN", font("Inter-SemiBold.otf", 26), (214, 220, 238, 255), 6)
        PW.spaced(d, W / 2, 76, f"{n_thrown(t)}", font("InterDisplay-Bold.otf", 84), (236, 120, 90, 255), 4)
    lab = None
    if HOOK <= t < T_V:
        lab = None
    elif t < T_F:
        lab = ("THE VICTIM", (160, 176, 210))
    elif t < T_B:
        lab = ("THE FIGHTER", ORANGE)
    elif t < T_END:
        lab = ("THE BUILDER", (236, 70, 60))
    if lab:
        PW.spaced(d, W / 2, 200, lab[0], font("InterDisplay-Bold.otf", 46), lab[1] + (255,), 6)
    if T_RH <= t < T_RH + 1.6:
        a = hq.pop(t, T_RH, 0.25) * (1 - smooth(prog(t, T_RH + 1.3, T_RH + 1.6)))
        text(im, W / 2, 330, "THEY THREW HARDER.", 80, a=min(1, a))
    for j, s_ in enumerate(("THEY THREW BRICKS.", "HE BUILT A CASTLE.")):
        a = smooth(prog(t, T_LINES + 0.8 * j, T_LINES + 0.8 * j + 0.4))
        if a > 0:
            text(im, W / 2, 140 + j * 86, s_, 68, col=(GOLD if j else (246, 240, 226)), a=a)
    for c in (HOOK, T_V, T_F, T_B):
        if c <= t < c + 0.06:
            im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), 0.4)
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


MUSIC = "Hitman.mp3"
HIT = 52.0   # lands on the end lines


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    put(out, track(MUSIC, HIT - T_LINES, DUR), 0.0, 1.8, fin=0.05, fout=1.0)
    # laughter-ish chatter in the hook
    for j in range(3):
        mix_in(out, noise(0.2, 4 + j, lo=300, hi=2500)[:int(0.2 * SR)] * env(int(0.2 * SR), 0.01, 0.12), 0.02 + j * 0.17, 0.3, 0.0)
    glass = noise(0.9, 9, lo=1500, hi=12000)[:int(0.9 * SR)] * env(int(0.9 * SR), 0.002, 0.7)
    mix_in(out, glass, 0.8, 0.8, 0.0)
    mix_in(out, tone(60, 0.5, (1, 2), a=0.001, d=0.4), 0.8, 0.6, 0.0)
    mix_in(out, tone(140, 0.15, (1, 2.5), a=0.001, d=0.1), 1.35, 0.5, 0.3)    # the catch
    for t0, d_, tg, w in THROWS:
        if t0 + d_ < DUR:
            mix_in(out, tone(120 + 30 * (hash(w) % 3), 0.1, (1, 2.4), a=0.001, d=0.07), t0 + d_, 0.18,
                   {"v": -0.6, "f": -0.2, "b": 0.5}[tg])
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.8, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "bricks"), exist_ok=True)
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [0.1, 0.84, 1.6, 3.5, 6.5, 9.0, 14.0, 20.0]
        sheet = Image.new("RGB", (360 * len(ts), 640))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS), (j * 360, 0))
        p = os.path.join(here, "bricks", "stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "bricks.mp4")
    wav = out + ".wav"
    write_wav(wav, audio())
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
