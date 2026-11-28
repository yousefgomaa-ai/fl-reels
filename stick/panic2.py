#!/usr/bin/env python3
"""PANIC vs CALM v2 - eleven situations where the motion itself is the meaning (real mocap, CMU), our night-stage look.

    python3 stick/panic2.py --stills [t ...]   # -> stick/panic/stills.png
    python3 stick/panic2.py stick/panic.mp4
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
from compare import ell, line, rrect, poly, figure, place, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import face, S, GOLD  # noqa
from money import put, track, text  # noqa
from tryagain2 import Seq, seg as _seg, clip  # noqa
from panic import facing_of  # noqa

FPS, SR = 30, 44100
L = 3.0
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
PANELS = {"P": (250, 1080), "C": (1090, 1920)}
GROUND = {k: a + 640 for k, (a, b) in PANELS.items()}
SC = S * 1.15
ORANGE = (240, 130, 40)
SCARF = (214, 44, 44)
GREY = (150, 154, 166)

WALK, RUN, TRIP, DIVE = "007/07_01", "009/09_01", "104/104_13", "090/90_16"
UPSET, CRY, SCARED, HAPPY, LAUGH = "079/79_74", "079/79_72", "079/79_73", "079/79_69", "079/79_70"
DRIVE, BOX_LIFT, BOX_PUSH, DRINK, WIPE, BRUSH = "079/79_76", "079/79_25", "081/81_06", "013/13_09", "013/13_20", "079/79_81"
ANGRYWALK, STOOL, JACKS, QUARREL, BOXING = "017/17_01", "013/13_01", "013/13_29", "018/18_10", "013/13_17"
SLIP, STUMBLE, PHONE, CHIN, BOARD = "090/90_17", "091/91_59", "079/79_36", "013/13_04", "079/79_31"


def sg(name, t0, t1, dur, lock="prev", **kw):
    """lock: a number = hips held there; 'prev' = held where the previous segment ended; None = the clip travels"""
    kw.setdefault("facing", facing_of(name, (t0 + t1) / 2))
    d = _seg(name, t0, t1, dur, **kw)
    d["_lock"] = lock
    return d


def mv(name, t0, t1, dur, **kw):
    return sg(name, t0, t1, dur, lock=None, **kw)


SITS = [
    ("STUCK IN TRAFFIC", "traffic",
     [sg(DRIVE, 2.0, 5.0, 3.0, 520)],
     [sg(DRIVE, 2.0, 4.0, 3.0, 520)]),
    ("HARD EXAM", "exam",
     [sg(UPSET, 2.2, 4.0, 1.4, 420), sg(CRY, 1.0, 3.4, 1.6)],
     [sg(CHIN, 9.0, 11.0, 1.2, 420), sg(BOARD, 1.0, 4.0, 1.8)]),
    ("WET FLOOR", "slip",
     [mv(SLIP, 2.0, 4.4, 2.0), sg(SLIP, 4.4, 4.9, 1.0)],
     [mv(WALK, 0.3, 2.1, 3.0)]),
    ("BAD NEWS", "phone",
     [sg(PHONE, 1.0, 2.6, 1.2, 480), sg(CRY, 1.0, 3.2, 1.8)],
     [sg(PHONE, 1.0, 3.4, 2.2, 480), sg(PHONE, 3.4, 3.4, 0.8)]),
    ("HEAVY BOX", "box",
     [sg(BOX_LIFT, 3.0, 4.4, 1.4, 420), sg(UPSET, 2.2, 3.8, 1.6)],
     [mv(BOX_PUSH, 1.3, 6.2, 3.0)]),
    ("SPILLED DRINK", "spill",
     [sg(DRINK, 1.4, 2.6, 1.0, 480), sg(SCARED, 2.0, 4.8, 2.0)],
     [sg(DRINK, 1.4, 2.6, 1.0, 480), sg(WIPE, 2.0, 6.0, 2.0)]),
    ("WOKE UP LATE", "late",
     [sg(RUN, 0.3, 1.04, 0.5, 480), sg(RUN, 0.3, 1.04, 0.5), sg(BRUSH, 1.0, 6.0, 2.0)],
     [sg(BRUSH, 1.0, 4.0, 3.0, 480)]),
    ("LONG LINE", "queue",
     [sg(ANGRYWALK, 2.0, 8.0, 3.0, 300)],
     [sg(STOOL, 1.6, 3.2, 3.0, 300)]),
    ("TRIPPED", "trip",
     [mv(WALK, 0.3, 1.1, 0.6), mv(TRIP, 0.62, 1.18, 0.5), sg(DIVE, 3.3, 3.95, 0.4, facing=-1), sg(DIVE, 3.95, 3.95, 1.5, facing=-1)],
     [mv(WALK, 0.3, 1.1, 0.6), mv(STUMBLE, 0.6, 1.6, 0.8), mv(WALK, 0.3, 1.9, 1.6)]),
    ("HARD WORKOUT", "gym",
     [sg(JACKS, 0.8, 2.4, 1.1, 480), sg(STOOL, 12.1, 14.5, 1.9)],
     [sg(JACKS, 0.8, 2.4, 1.0, 480), sg(JACKS, 0.8, 2.4, 1.0), sg(JACKS, 0.8, 2.4, 1.0)]),
    ("THEY LAUGHED", "laughed",
     [sg(QUARREL, 4.0, 6.0, 1.4, 380), sg(BOXING, 1.7, 4.2, 1.6)],
     [sg(LAUGH, 1.0, 3.0, 1.7, 380), mv(WALK, 0.3, 1.6, 1.3, facing=-1)]),
]
T_END = L * len(SITS)
DUR = T_END + 2.6
NF = int(round(DUR * FPS))
X0 = {"slip": 150, "box": 260, "trip": 150, "laughed": 380}


def build(segs, who, x0):
    done = []
    for k, sgm in enumerate(segs):
        s = dict(sgm, size=1.0)
        lk = s.pop("_lock")
        if lk == "prev":
            if done:
                prev = Seq(done, x0, floor=GROUND[who], scale=SC)
                s["lock"] = prev.pts(prev.dur - 1e-3)["hip"][0]
            else:
                s["lock"] = x0
        elif lk is not None:
            s["lock"] = lk
        done.append(s)
    return Seq(done, x0, floor=GROUND[who], scale=SC)


_SQ = {}


def SQ(i, who):
    if (i, who) not in _SQ:
        title, kind, p, c = SITS[i]
        _SQ[(i, who)] = build(p if who == "P" else c, who, X0.get(kind, 480))
    return _SQ[(i, who)]


def hand_mid(p):
    return ((p["hl"][0] + p["hr"][0]) / 2, (p["hl"][1] + p["hr"][1]) / 2)


def high_hand(p):
    return p["hl"] if p["hl"][1] < p["hr"][1] else p["hr"]


# ---------------------------------------------------------------- props (back = behind the figure, front = over it)
def props(kind, who, d, st, u, p, front):
    g = GROUND[who]
    if kind == "traffic":
        hx, hy = p["hip"]
        if not front:
            for j, cx in enumerate((860, 1060)):      # stopped cars ahead
                rrect(d, (cx - 110, g - 110, cx + 110, g - 20), 18, (70, 74, 90, 255))
                ell(d, cx - 104, g - 70, 8, 6, (240, 60, 50, 255))
                for wx in (cx - 60, cx + 60):
                    ell(d, wx, g - 18, 22, 22, (20, 20, 24, 255))
        else:
            col = (200, 70, 60) if who == "P" else (60, 120, 200)
            rrect(d, (hx - 220, hy - 10, hx + 200, g - 18), 22, col + (255,), outline=(30, 30, 36, 255), w=3)
            poly(d, [(hx + 60, hy - 10), (hx + 120, hy - 90), (hx + 140, hy - 90), (hx + 110, hy - 10)], (150, 190, 230, 200))
            for wx in (hx - 140, hx + 120):
                ell(d, wx, g - 18, 34, 34, (20, 20, 24, 255))
                ell(d, wx, g - 18, 14, 14, (170, 172, 180, 255))
            if who == "P" and int(u * 4) % 2 == 0:
                PW.spaced(d, (hx + 260) * K, (hy - 120) * K, "BEEP!", font("InterDisplay-Bold.otf", 40 * K), (250, 220, 80, 255), 2)
            if who == "C":
                for j in range(3):
                    v = (u * 0.7 + j / 3) % 1
                    PW.spaced(d, (hx + 40 + 30 * j) * K, (hy - 170 - 120 * v) * K, "♪", font("InterDisplay-Bold.otf", 40 * K),
                              (240, 220, 160, int(255 * (1 - v))), 0)
    elif kind == "exam" and not front:
        rrect(d, (620, g - 430, 960, g - 180), 8, (30, 50, 40, 255), outline=(120, 90, 60, 255), w=8)
        if who == "P":
            PW.spaced(d, 790 * K, (g - 305) * K, "???", font("InterDisplay-Bold.otf", 80 * K), (240, 240, 240, 255), 4)
        else:
            sq = SQ(1, "C")
            w = clamp((u - sq.starts[1]) / sq.segs[1]["dur"])
            for j in range(int(5 * w) + 1):
                line(d, [(650, g - 400 + j * 40), (650 + min(1, 5 * w - j) * 280, g - 400 + j * 40)], (230, 230, 230, 255), 4)
            rrect(d, (320, g - 120, 420, g - 100), 4, (100, 80, 60, 255))
    elif kind == "slip" and not front:
        ell(d, 640, g + 2, 130, 12, (90, 140, 210, 255))
        poly(d, [(820, g), (850, g - 110), (880, g)], (240, 200, 40, 255))
        PW.spaced(d, 850 * K, (g - 40) * K, "!", font("InterDisplay-Bold.otf", 40 * K), (20, 20, 20, 255), 0)
    elif kind == "phone" and front:
        hx, hy = high_hand(p)
        rrect(d, (hx - 10, hy - 26, hx + 10, hy + 8), 4, (20, 20, 26, 255), outline=(120, 120, 130, 255), w=2)
        if who == "P" and u > 1.3:
            PW.spaced(d, (p["head"][0] + 90) * K, (p["head"][1] - 70) * K, "NO...", font(SERIF, 36 * K), (236, 228, 210, 255), 3)
    elif kind == "box":
        if who == "P":
            if not front:
                rrect(d, (560, g - 150, 760, g), 6, (150, 110, 70, 255), outline=(80, 56, 36, 255), w=3)
                PW.spaced(d, 660 * K, (g - 75) * K, "HEAVY", font("InterDisplay-Bold.otf", 30 * K), (40, 30, 20, 255), 3)
        elif front:
            hx = max(p["hl"][0], p["hr"][0])
            rrect(d, (hx + 4, g - 150, hx + 204, g), 6, (150, 110, 70, 255), outline=(80, 56, 36, 255), w=3)
            PW.spaced(d, (hx + 104) * K, (g - 75) * K, "HEAVY", font("InterDisplay-Bold.otf", 30 * K), (40, 30, 20, 255), 3)
    elif kind == "spill" and front:
        sq = SQ(5, who)
        nx, ny = p["neck"]
        if u < sq.segs[0]["dur"]:
            hx, hy = high_hand(p)
            rrect(d, (hx - 12, hy - 30, hx + 12, hy + 6), 4, (240, 240, 245, 255), outline=(150, 150, 160, 255), w=2)
        stain = 1.0 if who == "P" else 1 - smooth(clamp((u - 1.2) / 1.6))
        if u > 0.75 and stain > 0:
            ell(d, nx + 4, ny + 40, 22, 18, (120, 80, 40, int(220 * stain)))
            if who == "P" and u < 1.3:
                for j in range(6):
                    ell(d, nx + 10 + 14 * j, ny + 30 + 30 * (u - 0.75) * j, 4, 6, (140, 90, 50, 255))
    elif kind == "late":
        if not front:
            rrect(d, (780, g - 420, 960, g - 330), 10, (20, 20, 26, 255))
            col = (240, 80, 80) if who == "P" else (200, 204, 214)
            PW.spaced(d, 870 * K, (g - 375) * K, "8:59" if who == "P" else "7:00", font("InterDisplay-Bold.otf", 52 * K), col + (255,), 2)
            if who == "P" and int(u * 6) % 2 == 0:
                for j in range(3):
                    line(d, [(970 + 10 * j, g - 430 - 8 * j), (990 + 12 * j, g - 450 - 10 * j)], (240, 80, 80, 255), 4)
        else:
            sq = SQ(6, who)
            if u >= sq.starts[-1]:
                hx, hy = high_hand(p)
                line(d, [(hx, hy), (hx + 26, hy - 30)], (120, 200, 240, 255), 6)
    elif kind == "queue" and not front:
        for j, x in enumerate((640, 760, 880, 1000)):
            q = place(PW.STAND, (x, g - 113 * SC), -1, SC)
            figure(st, q, SC, light=(0.4, -0.9), body=GREY)
    elif kind == "laughed" and not front:
        for j, (x, nm) in enumerate(((800, LAUGH), (960, "014/14_17"))):
            q = clip(nm).pts(1.5 + (u * 1.2 + j * 0.4) % 2.0, x0=0, floor=g, scale=SC, x_lock=x, facing=-1)
            figure(st, q, SC, light=(0.4, -0.9), body=GREY)
            face(ImageDraw.Draw(st), q, "laugh", -1, u)
            PW.spaced(d, q["head"][0] * K, (q["head"][1] - 70 + 8 * math.sin(u * 14 + j)) * K, "HAHA",
                      font("InterDisplay-Bold.otf", 30 * K), (255, 255, 255, 255), 2)


# ---------------------------------------------------------------- the look
_C = {}


def panel_back(who):
    if who not in _C:
        a, b = PANELS[who]
        g = GROUND[who]
        im = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        top, bot = ((14, 12, 20), (30, 26, 38)) if who == "P" else ((10, 14, 22), (22, 30, 44))
        for j in range(40):
            y0 = a + (g - a) * j / 40
            y1 = a + (g - a) * (j + 1) / 40
            col = tuple(int(lerp(top[k], bot[k], j / 39)) for k in range(3))
            d.rectangle((0, y0 * K, W * K, y1 * K + 1), col + (255,))
        d.rectangle((0, g * K, W * K, b * K), (14, 14, 20, 255))
        cone = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(cone).polygon([(470 * K, a * K), (610 * K, a * K), (900 * K, g * K), (180 * K, g * K)], (255, 240, 220, 34))
        im.alpha_composite(cone.filter(ImageFilter.GaussianBlur(14 * K)))
        pool = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(pool).ellipse((140 * K, (g - 30) * K, 940 * K, (g + 70) * K), (255, 240, 220, 40))
        im.alpha_composite(pool.filter(ImageFilter.GaussianBlur(20 * K)))
        line(d, [(0, g), (W, g)], (70, 70, 86, 255), 3)
        _C[who] = im
    return _C[who]


def expr(kind, who, u):
    if who == "C":
        return "happy" if kind != "exam" or u > 1.2 else "neutral"
    return {"traffic": "angry", "exam": "cry" if u > 1.4 else "nervous", "slip": "shocked" if u < 2.0 else "cry",
            "phone": "cry" if u > 1.2 else "neutral", "box": "tired", "spill": "shocked", "late": "nervous",
            "queue": "angry", "trip": "shocked" if u < 1.5 else "cry", "gym": "tired", "laughed": "angry"}[kind]


def draw_panel(st, i, who, u):
    title, kind, _, _ = SITS[i]
    a, b = PANELS[who]
    g = GROUND[who]
    st.alpha_composite(panel_back(who).crop((0, a * K, W * K, b * K)), (0, a * K))
    lay = Image.new("RGBA", st.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    sq = SQ(i, who)
    p = sq.pts(min(u, sq.dur - 1e-3))
    ell(d, p["hip"][0], g + 4, 70, 12, (0, 0, 0, 110))
    props(kind, who, d, lay, u, p, False)
    figure(lay, p, SC, light=(0.4, -0.9), body=(236, 238, 244))
    dd = ImageDraw.Draw(lay)
    f = 1 if p["head"][0] >= p["neck"][0] else -1
    face(dd, p, expr(kind, who, u), f, u)
    if who == "P":
        hx, hy = p["head"]
        line(dd, [(hx - 30, hy - 12), (hx + 30, hy - 12)], ORANGE + (255,), 8)
    else:
        nx, ny = p["neck"]
        ell(dd, nx, ny + 2, 21 * SC / S, 11 * SC / S, SCARF + (255,))
        poly(dd, [(nx, ny), (nx - f * 44, ny + 26), (nx - f * 30, ny + 40)], SCARF + (255,))
    props(kind, who, dd, lay, u, p, True)
    # glossy floor: a faded reflection
    band = lay.crop((0, (g - (b - g)) * K, W * K, g * K)).transpose(Image.FLIP_TOP_BOTTOM)
    band = band.filter(ImageFilter.GaussianBlur(3 * K))
    al = np.asarray(band.split()[3], np.float32) * np.linspace(0.28, 0.0, band.size[1], dtype=np.float32)[:, None]
    band.putalpha(Image.fromarray(al.astype(np.uint8)))
    st.alpha_composite(band, (0, g * K))
    st.alpha_composite(lay.crop((0, a * K, W * K, b * K)), (0, a * K))


def frame(t):
    st = Image.new("RGBA", (W * K, H * K), (6, 6, 10, 255))
    end = t >= T_END
    i = min(len(SITS) - 1, int(t / L))
    u = (t - i * L) if not end else L - 0.01
    for who in ("P", "C"):
        draw_panel(st, i, who, u)
    im = st.resize((W, H), Image.LANCZOS)
    dd = ImageDraw.Draw(im)
    PW.spaced(dd, W / 2, 34, "PANIC  vs  CALM", font("InterDisplay-Bold.otf", 62), (246, 246, 250, 255), 6)
    PW.spaced(dd, W / 2, 130, SITS[i][0], font(SERIF, 46), GOLD + (255,), 5)
    PW.spaced(dd, W / 2, 196, f"{i + 1}/{len(SITS)}", font("Inter-SemiBold.otf", 24), (170, 176, 196, 255), 6)
    PW.spaced(dd, 100, PANELS["P"][0] + 28, "PANIC", font("InterDisplay-Bold.otf", 40), ORANGE + (255,), 5)
    PW.spaced(dd, 90, PANELS["C"][0] + 28, "CALM", font("InterDisplay-Bold.otf", 40), (236, 238, 246, 255), 5)
    dd.line((0, PANELS["C"][0] - 5, W, PANELS["C"][0] - 5), (50, 52, 64), 3)
    if end:
        v = t - T_END
        im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (0, 0, 0)), 0.78 * smooth(clamp(v / 0.4))).convert("RGBA")
        text(im, W / 2, 780, "THE PROBLEM", 92, a=smooth(prog(v, 0.2, 0.5)))
        text(im, W / 2, 890, "WASN'T THE PROBLEM.", 80, a=smooth(prog(v, 0.35, 0.65)))
        text(im, W / 2, 1060, "THE PANIC WAS.", 96, col=GOLD, a=smooth(prog(v, 1.0, 1.3)))
    for k_ in range(1, len(SITS)):
        if abs(t - k_ * L) < 0.06:
            im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 80)))
    return np.asarray(im.convert("RGB"))


def render(i):
    acc = None
    for k_ in range(2):
        f = frame((i + k_ / 4) / FPS).astype(np.float32)
        acc = f if acc is None else acc + f
    return (acc / 2).astype(np.uint8).tobytes()


MUSIC = "Hitman.mp3"


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    put(out, track(MUSIC, 20.0, DUR), 0.0, 1.5, fin=0.05, fout=1.0)
    for i, (title, kind, _, _) in enumerate(SITS):
        s0 = i * L
        mix_in(out, tone(1320, 0.5, (1, 2, 3), a=0.002, d=0.45), s0 + 1.8, 0.22, 0.5)
        if kind in ("slip", "trip"):
            mix_in(out, noise(0.3, 9, lo=40, hi=900)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.002, 0.25), s0 + 1.45, 0.7, -0.5)
        if kind == "traffic":
            for k_ in range(3):
                mix_in(out, tone(440, 0.22, (1, 1.5), a=0.005, d=0.05), s0 + 0.3 + k_ * 0.5, 0.25, -0.5)
        if kind == "laughed":
            mix_in(out, noise(1.4, 4, lo=300, hi=2500)[:int(1.4 * SR)] * env(int(1.4 * SR), 0.05, 0.8), s0 + 0.1, 0.25, 0.5)
        if i:
            mix_in(out, noise(0.3, 9, lo=500, hi=7000)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.15, 0.1), s0 - 0.15, 0.15, 0.0)
    mix_in(out, tone(55, 1.0, (1, 2), a=0.002, d=0.9), T_END + 1.0, 0.5, 0.0)
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.7, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "panic"), exist_ok=True)
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [i * L + o for i in range(len(SITS)) for o in (0.8, 2.4)] + [T_END + 2.2]
        cols = 8
        rows = math.ceil(len(ts) / cols)
        sheet = Image.new("RGB", (200 * cols, 356 * rows))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((200, 356), Image.LANCZOS), ((j % cols) * 200, (j // cols) * 356))
        p = os.path.join(here, "panic", "stills.png")
        sheet.save(p)
        print(p, round(DUR, 1))
        return
    out = sys.argv[1]
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
