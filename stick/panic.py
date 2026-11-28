#!/usr/bin/env python3
"""PANIC vs CALM - same problem, two ways. Five situations, real motion capture (CMU).

door (PUSH... it says PULL) - jar - puddle - phone at 1% - exam.
THE PROBLEM WASN'T THE PROBLEM. / THE PANIC WAS.

    python3 stick/panic.py --stills [t ...]   # -> stick/panic/stills.png
    python3 stick/panic.py stick/panic.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import hq  # noqa
from compare import ell, line, rrect, poly, figure, place, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import face, S, GOLD  # noqa
from money import put, track, text  # noqa
from tryagain2 import Seq, seg as _seg, clip, shift  # noqa

FPS, SR = 30, 44100
L = 4.8
SITS = ["door", "jar", "puddle", "phone", "exam"]
T_END = L * len(SITS)
DUR = T_END + 2.6
NF = int(round(DUR * FPS))
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
PANELS = {"P": (230, 1070), "C": (1080, 1920)}       # y range of each half
GROUND = {k: a + 660 for k, (a, b) in PANELS.items()}
SC = S * 1.12
RED = (226, 70, 60)
TEAL = (70, 200, 180)

WALK, STRIKE, KICK, UPSET, CRY, HAPPY = "007/07_01", "002/02_05", "010/10_01", "079/79_74", "079/79_72", "079/79_69"
JAR, SEARCH, PHONE, SCOOP, LJ, RUN = "013/13_07", "079/79_07", "079/79_36", "002/02_06", "083/83_42", "009/09_01"


def facing_of(name, t):
    c = clip(name)
    f = c.frame(t)
    toe = c._2d("toel", f) - c._2d("fl", f)
    d = c.J["hip"][-1] - c.J["hip"][0]
    if np.hypot(d[0], d[2]) > 40:      # a clip that travels: projected so travel goes +x
        return 1
    return 1 if toe[0] >= 0 else -1


def seg(name, t0, t1, dur, **kw):
    kw.setdefault("facing", facing_of(name, (t0 + t1) / 2))
    return _seg(name, t0, t1, dur, **kw)


def stay(name, t0, t1, dur, x, **kw):
    """an in-place clip, hips held at x"""
    return seg(name, t0, t1, dur, lock=x, **kw)


# ---------------------------------------------------------------- the five situations
DOOR_X = 760
PUD = (470, 720)


def plans():
    P, C = {}, {}
    # 1 door
    P["door"] = [seg(WALK, 0.3, 1.45, 0.9), stay(STRIKE, 1.0, 1.75, 0.5, 600), stay(STRIKE, 1.0, 1.75, 0.45, 600),
                 stay(KICK, 4.3, 5.05, 0.6, 600), stay(STRIKE, 1.0, 1.75, 0.4, 600), stay(UPSET, 2.2, 3.7, 1.6, 600)]
    C["door"] = [seg(WALK, 0.3, 1.45, 0.9), stay(PHONE, 1.2, 1.8, 0.7, 600), seg(WALK, 0.3, 1.6, 1.1), stay(HAPPY, 0.3, 0.9, 1.8, 900)]
    # 2 jar
    P["jar"] = [stay(JAR, 2.5, 5.0, 1.5, 480), stay(STRIKE, 1.0, 1.75, 0.5, 480), stay(STRIKE, 1.0, 1.75, 0.5, 480),
                stay(CRY, 1.0, 3.6, 2.0, 480)]
    C["jar"] = [stay(JAR, 2.5, 4.0, 0.8, 480), stay(JAR, 6.0, 9.5, 2.4, 480), stay(HAPPY, 0.3, 0.9, 1.4, 480)]
    # 3 puddle
    P["puddle"] = [seg(WALK, 0.3, 0.95, 0.5), seg(LJ, 1.8, 3.6, 1.4), stay(UPSET, 2.2, 3.9, 2.6, 0)]
    C["puddle"] = [seg(WALK, 0.3, 2.55, 2.3), stay(HAPPY, 0.3, 0.9, 2.3, 0)]
    # 4 phone
    P["phone"] = [stay(SEARCH, 0.8, 2.5, 1.1, 360), seg(RUN, 0.3, 1.04, 0.45), stay(SEARCH, 0.8, 2.5, 1.0, 0),
                  stay(UPSET, 2.2, 3.9, 2.0, 0)]
    C["phone"] = [stay(PHONE, 0.9, 2.6, 1.4, 480), stay(PHONE, 2.6, 3.4, 3.2, 480)]
    # 5 exam
    P["exam"] = [stay(UPSET, 2.2, 4.6, 2.0, 420), stay(CRY, 1.0, 3.6, 2.6, 420)]
    C["exam"] = [stay(SCOOP, 0.9, 2.5, 0.85, 480) for _ in range(4)] + [stay(HAPPY, 0.3, 0.9, 1.3, 480)]
    return P, C


PLAN_P, PLAN_C = plans()


def make_seq(segs, who, x0):
    return Seq([dict(s, size=1.0) for s in segs], x0, floor=GROUND[who], scale=SC)


def seq_for(sit, who):
    segs = (PLAN_P if who == "P" else PLAN_C)[sit]
    if sit == "puddle" and who == "P":     # land in the middle of the puddle
        probe = make_seq(segs, who, 0)
        land = probe.starts[1] + segs[1]["dur"] * 0.82
        x0 = (PUD[0] + PUD[1]) / 2 - probe.pts(land)["hip"][0]
        s = make_seq(segs, who, x0)
        s.segs[2]["lock"] = s.pts(probe.starts[2] - 0.01)["hip"][0]
        return make_seq(s.segs, who, x0)
    if sit == "puddle":
        probe = make_seq(segs, who, 0)
        x0 = 160 - probe.pts(0)["hip"][0] + probe.pts(0)["hip"][0]
        s = make_seq(segs, who, 160)
        s.segs[1]["lock"] = s.pts(segs[0]["dur"] - 0.01)["hip"][0]
        return make_seq(s.segs, who, 160)
    if sit == "door":
        x0 = 230
        s = make_seq(segs, who, x0)
        if who == "C":
            s.segs[3]["lock"] = s.pts(s.starts[3] - 0.01)["hip"][0]
            return make_seq(s.segs, who, x0)
        return s
    if sit == "phone" and who == "P":
        s = make_seq(segs, who, 360)
        end = s.pts(s.starts[2] - 0.01)["hip"][0]
        s.segs[2]["lock"] = end
        s.segs[3]["lock"] = end
        return make_seq(s.segs, who, 360)
    return make_seq(segs, who, 480)


_SQ = {}


def SQ(sit, who):
    if (sit, who) not in _SQ:
        _SQ[(sit, who)] = seq_for(sit, who)
    return _SQ[(sit, who)]


SOLVE_C = {"door": 1.7, "jar": 0.85, "puddle": 2.3, "phone": 1.4, "exam": 3.4}
RESULT_P = {"door": "4:12", "jar": "9:47", "puddle": "SOAKED", "phone": "32:00", "exam": "GAVE UP"}
SOLVE_TXT_C = {"door": "0:02", "jar": "0:01", "puddle": "0:03", "phone": "0:02", "exam": "DONE"}


def hand_mid(p):
    return ((p["hl"][0] + p["hr"][0]) / 2, (p["hl"][1] + p["hr"][1]) / 2)


# ---------------------------------------------------------------- props
def door(d, who, u, p):
    g = GROUND[who]
    x = DOOR_X
    rrect(d, (x - 10, g - 330, x + 150, g), 6, (60, 50, 44, 255))        # the frame
    openk = 0.0
    shake = 0.0
    if who == "C":
        openk = smooth(clamp((u - 1.25) / 0.35))
    else:
        sq = SQ("door", "P")
        for k_ in (1, 2, 3, 4):
            t_hit = sq.starts[k_] + sq.segs[k_]["dur"] * 0.55
            if t_hit <= u < t_hit + 0.25:
                shake = 6 * math.sin((u - t_hit) * 90) * (1 - (u - t_hit) / 0.25)
    wdt = 140 * (1 - 0.85 * openk)
    rrect(d, (x + shake, g - 320, x + wdt + shake, g), 4, (150, 108, 70, 255), outline=(90, 60, 40, 255), w=3)
    if openk < 0.6:
        rrect(d, (x + 20 + shake, g - 230, x + 120 + shake, g - 190), 4, (240, 236, 220, 255))
        PW.spaced(d, (x + 70 + shake) * K, (g - 210) * K, "PULL", font("InterDisplay-Bold.otf", 24 * K), (30, 30, 34, 255), 3)
        ell(d, x + 18 + shake, g - 150, 7, 7, (220, 200, 120, 255))
    else:
        poly(d, [(x + 30, g - 320), (x + 250, g - 260), (x + 250, g + 20), (x + 30, g)], (96, 88, 66, 255))


def jar(d, who, u, p):
    sq = SQ("jar", who)
    g = GROUND[who]
    if who == "P":
        t_break = sq.starts[2] + sq.segs[2]["dur"] * 0.55
        if u < sq.starts[1]:
            hx, hy = hand_mid(p)
            rrect(d, (hx - 22, hy - 30, hx + 22, hy + 16), 8, (180, 220, 240, 200), outline=(120, 160, 190, 255), w=2)
            rrect(d, (hx - 24, hy - 38, hx + 24, hy - 26), 3, (200, 60, 50, 255))
        elif u < t_break:
            jx, jy = 640, g - 140
            rrect(d, (560, g - 120, 720, g), 4, (110, 80, 60, 255))
            rrect(d, (jx - 22, jy - 30, jx + 22, jy + 16), 8, (180, 220, 240, 200), outline=(120, 160, 190, 255), w=2)
            rrect(d, (jx - 24, jy - 38, jx + 24, jy - 26), 3, (200, 60, 50, 255))
            hx, hy = p["hr"]
            line(d, [(hx, hy), (hx + 34, hy - 40)], (130, 90, 50, 255), 6)
            rrect(d, (hx + 20, hy - 60, hx + 56, hy - 38), 3, (90, 92, 100, 255))
        else:
            rrect(d, (560, g - 120, 720, g), 4, (110, 80, 60, 255))
            v = u - t_break
            rng = np.random.default_rng(3)
            for _ in range(14):
                a = rng.uniform(-3, 0)
                r = 160 * min(1, v * 3)
                sx, sy = 640 + r * math.cos(a), g - 140 + r * math.sin(a) + 600 * min(v, 0.3) ** 2
                poly(d, [(sx, sy), (sx + 10, sy + 4), (sx + 3, sy + 12)], (180, 220, 240, 230))
            PW.spaced(d, 640 * K, (g - 210) * K, "CRASH!", font("InterDisplay-Bold.otf", 40 * K), (240, 200, 90, int(255 * clamp(1 - v))), 3)
    else:
        hx, hy = hand_mid(p)
        rrect(d, (hx - 22, hy - 30, hx + 22, hy + 16), 8, (180, 220, 240, 200), outline=(120, 160, 190, 255), w=2)
        if u < SOLVE_C["jar"]:
            rrect(d, (hx - 24, hy - 38, hx + 24, hy - 26), 3, (200, 60, 50, 255))
        else:
            rrect(d, (hx + 30, hy - 10, hx + 78, hy + 2), 3, (200, 60, 50, 255))


def puddle(d, who, u, p):
    g = GROUND[who]
    off = 60 if who == "C" else 0         # calm's puddle is a step closer to us: he walks behind it
    ell(d, (PUD[0] + PUD[1]) / 2, g + off, (PUD[1] - PUD[0]) / 2, 18, (70, 120, 190, 220))
    ell(d, (PUD[0] + PUD[1]) / 2 - 40, g + off - 4, 60, 5, (190, 220, 255, 160))
    if who == "P":
        sq = SQ("puddle", "P")
        land = sq.starts[1] + sq.segs[1]["dur"] * 0.82
        if u >= land:
            v = u - land
            rng = np.random.default_rng(5)
            for _ in range(24):
                a = rng.uniform(math.pi * 1.1, math.pi * 1.9)
                r = 180 * min(1, v * 3) * rng.uniform(0.5, 1)
                ell(d, (PUD[0] + PUD[1]) / 2 + r * math.cos(a), g + r * math.sin(a) + 500 * min(v, 0.5) ** 2, 5, 5,
                    (150, 190, 240, int(230 * clamp(1 - v * 1.5))))
            for j in range(4):   # dripping
                hx, hy = p["hl"] if j % 2 else p["hr"]
                vv = (u * 2 + j / 4) % 1
                ell(d, hx, hy + 40 * vv, 3, 5, (150, 190, 240, int(220 * (1 - vv))))


def battery(d, x, y, pct, col, blink=1.0):
    rrect(d, (x - 50, y - 24, x + 44, y + 24), 6, (20, 20, 26, int(255 * blink)), outline=col + (int(255 * blink),), w=4)
    rrect(d, (x + 44, y - 10, x + 54, y + 10), 2, col + (int(255 * blink),))
    rrect(d, (x - 44, y - 18, x - 44 + 82 * pct, y + 18), 3, col + (int(255 * blink),))


def phone(d, who, u, p):
    hx, hy = p["head"]
    if who == "P":
        blink = 0.4 + 0.6 * (int(u * 4) % 2)
        battery(d, hx, hy - 110, 0.03, RED, blink)
        PW.spaced(d, hx * K, (hy - 160) * K, "1%", font("InterDisplay-Bold.otf", 34 * K), RED + (int(255 * blink),), 2)
        rng = np.random.default_rng(int(u * 3))
        for j in range(3):
            PW.spaced(d, (hx + rng.uniform(-90, 90)) * K, (hy - 60 - rng.uniform(0, 60)) * K, "?",
                      font("InterDisplay-Bold.otf", 46 * K), (240, 240, 245, 220), 0)
    else:
        ch = u >= SOLVE_C["phone"]
        pct = 0.03 + 0.9 * smooth(clamp((u - SOLVE_C["phone"]) / 2.5)) if ch else 0.03
        battery(d, hx, hy - 110, pct, (90, 210, 110) if ch else RED)
        PW.spaced(d, hx * K, (hy - 160) * K, f"{int(pct * 100) + 1}%", font("InterDisplay-Bold.otf", 34 * K),
                  ((90, 210, 110) if ch else RED) + (255,), 2)
        if ch:
            bx, by = p["hl"]
            rrect(d, (bx - 16, by - 26, bx + 16, by + 26), 5, (40, 44, 56, 255), outline=(90, 210, 110, 255), w=2)
            line(d, [(bx, by - 26), p["hr"]], (230, 230, 236, 255), 3)


def exam(d, who, u, p):
    g = GROUND[who]
    if who == "P":
        for j in range(12):
            rrect(d, (640 + (j % 2) * 8, g - 26 - j * 26, 800 + (j % 2) * 8, g - j * 26), 3,
                  [(170, 60, 60), (60, 110, 170), (200, 160, 60)][j % 3] + (255,), outline=(30, 30, 36, 255), w=1.5)
        PW.spaced(d, 720 * K, (g - 350) * K, "EXAM", font("InterDisplay-Bold.otf", 40 * K), RED + (255,), 4)
        rng = np.random.default_rng(int(u * 6))
        for _ in range(6):   # papers flying
            x, y = rng.uniform(150, 900), rng.uniform(g - 500, g - 60)
            rrect(d, (x, y, x + 34, y + 44), 2, (240, 238, 230, 200))
    else:
        moved = min(4, int(u / 0.85))
        rrect(d, (620, g - 26 * (12 - moved * 3), 780, g), 3, (110, 120, 150, 255), outline=(30, 30, 36, 255), w=1.5)
        for j in range(moved):
            rrect(d, (200, g - 26 * (j + 1) * 3, 330, g - 26 * j * 3), 3, (90, 180, 120, 255), outline=(30, 30, 36, 255), w=1.5)
        PW.spaced(d, 700 * K, (g - 26 * (12 - moved * 3) - 30) * K, "EXAM", font("InterDisplay-Bold.otf", 30 * K), (200, 204, 220, 255), 3)
        PW.spaced(d, 265 * K, (g - 26 * moved * 3 - 30) * K, f"DONE {moved}/4", font("InterDisplay-Bold.otf", 26 * K), (90, 210, 110, 255), 2)
        if 0 < u % 0.85 < 0.6 and u < 3.4:
            hx, hy = hand_mid(p)
            rrect(d, (hx - 40, hy - 14, hx + 40, hy + 10), 3, (110, 120, 150, 255))


PROPS = {"door": door, "jar": jar, "puddle": puddle, "phone": phone, "exam": exam}
FRONT = {"jar", "phone", "exam"}        # props drawn over the figure


# ---------------------------------------------------------------- frame
def who_expr(sit, who, u, dur):
    if who == "C":
        return "happy" if u > SOLVE_C[sit] else "neutral"
    return "angry" if u < dur * 0.45 else ("cry" if sit in ("jar", "exam") else "sad")


def draw_panel(st, d, sit, who, u):
    a, b = PANELS[who]
    g = GROUND[who]
    poly(d, [(0, a), (W, a), (W, b), (0, b)], (24, 20, 30, 255) if who == "P" else (16, 26, 30, 255))
    poly(d, [(540 - 60, a), (540 + 60, a), (540 + 380, g), (540 - 380, g)], (40, 36, 50, 255) if who == "P" else (30, 46, 50, 255))
    poly(d, [(0, g), (W, g), (W, b), (0, b)], (34, 30, 40, 255) if who == "P" else (26, 36, 40, 255))
    line(d, [(0, g), (W, g)], (80, 80, 96, 255), 3)
    sq = SQ(sit, who)
    p = sq.pts(min(u, sq.dur - 1e-3))
    ell(d, p["hip"][0], g + 4, 70, 12, (0, 0, 0, 100))
    if sit not in FRONT:
        PROPS[sit](d, who, u, p)
    figure(st, p, SC, light=(0.4, -0.9))
    dd = ImageDraw.Draw(st)
    f = sq.segs[0].get("facing", 1)
    face(dd, p, who_expr(sit, who, u, L), 1 if p["head"][0] >= p["neck"][0] else -1, u)
    if who == "P":   # red sweatband = panic, teal = calm
        hx, hy = p["head"]
        line(dd, [(hx - 30, hy - 12), (hx + 30, hy - 12)], RED + (255,), 7)
    else:
        nx, ny = p["neck"]
        ell(dd, nx, ny + 2, 20, 10, TEAL + (255,))
    if sit in FRONT:
        PROPS[sit](d, who, u, p)
    return p


def frame(t):
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    poly(d, [(0, 0), (W, 0), (W, H), (0, H)], (8, 8, 12, 255))
    end = t >= T_END
    i = min(len(SITS) - 1, int(t / L))
    sit = SITS[i]
    u = (t - i * L) if not end else L - 0.01
    for who in ("P", "C"):
        draw_panel(st, d, sit, who, u)
    im = st.resize((W, H), Image.LANCZOS)
    dd = ImageDraw.Draw(im)
    # header
    PW.spaced(dd, W / 2, 40, "PANIC  vs  CALM", font("InterDisplay-Bold.otf", 64), (246, 246, 250, 255), 6)
    PW.spaced(dd, W / 2, 140, f"PROBLEM {i + 1}/5", font("Inter-SemiBold.otf", 28), (180, 186, 204, 255), 6)
    for who, col in (("P", RED), ("C", TEAL)):
        a, b = PANELS[who]
        PW.spaced(dd, 90, a + 30, "PANIC" if who == "P" else "CALM", font("InterDisplay-Bold.otf", 40), col + (255,), 5)
        # the clock
        if who == "C":
            solved = u >= SOLVE_C[sit]
            s_ = SOLVE_TXT_C[sit] if solved else f"0:0{int(u)}"
            colr = (90, 210, 110) if solved else (236, 238, 246)
            PW.spaced(dd, W - 150, a + 30, s_ + (" ✓" if solved else ""), font("InterDisplay-Bold.otf", 44), colr + (255,), 2)
        else:
            if u < L - 1.3:
                mins = u / (L - 1.3) * 4
                s_ = f"{int(mins)}:{int((mins % 1) * 60):02d}"
                colr = (236, 238, 246)
            else:
                s_ = RESULT_P[sit] + " ✗"
                colr = RED
            PW.spaced(dd, W - 170, a + 30, s_, font("InterDisplay-Bold.otf", 44), colr + (255,), 2)
    line(dd, [(0, PANELS["C"][0]), (W, PANELS["C"][0])], (60, 62, 74), 4)
    if end:
        v = t - T_END
        im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (0, 0, 0)), 0.75 * smooth(clamp(v / 0.4))).convert("RGBA")
        text(im, W / 2, 780, "THE PROBLEM", 92, a=smooth(prog(v, 0.2, 0.5)))
        text(im, W / 2, 890, "WASN'T THE PROBLEM.", 80, a=smooth(prog(v, 0.35, 0.65)))
        text(im, W / 2, 1060, "THE PANIC WAS.", 96, col=GOLD, a=smooth(prog(v, 1.0, 1.3)))
    for k_ in range(1, len(SITS)):
        if abs(t - k_ * L) < 0.07:
            im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 90)))
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
    thud = noise(0.22, 3, lo=60, hi=1200)[:int(0.22 * SR)] * env(int(0.22 * SR), 0.002, 0.16)
    ding = tone(1320, 0.5, (1, 2, 3), a=0.002, d=0.45)
    buzz = tone(110, 0.3, (1, 2, 3), a=0.005, d=0.25)
    for i, sit in enumerate(SITS):
        s0 = i * L
        mix_in(out, ding, s0 + SOLVE_C[sit], 0.3, 0.5)
        mix_in(out, buzz, s0 + L - 1.3, 0.35, -0.5)
        sq = SQ(sit, "P")
        for k_ in range(1, len(sq.segs)):
            mix_in(out, thud, s0 + sq.starts[k_] + sq.segs[k_]["dur"] * 0.55, 0.3, -0.5)
        if sit == "jar":
            mix_in(out, noise(0.6, 8, lo=1500, hi=11000)[:int(0.6 * SR)] * env(int(0.6 * SR), 0.002, 0.5),
                   s0 + sq.starts[2] + sq.segs[2]["dur"] * 0.55, 0.6, -0.5)
        if sit == "puddle":
            mix_in(out, noise(0.8, 9, lo=200, hi=5000)[:int(0.8 * SR)] * env(int(0.8 * SR), 0.01, 0.6),
                   s0 + sq.starts[1] + sq.segs[1]["dur"] * 0.82, 0.6, -0.5)
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
        ts = [float(a) for a in sys.argv[2:]] or [i * L + o for i in range(5) for o in (0.6, 1.8, 3.0, 4.5)] + [T_END + 2.0]
        cols = 7
        rows = math.ceil(len(ts) / cols)
        sheet = Image.new("RGB", (210 * cols, 373 * rows))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((210, 373), Image.LANCZOS), ((j % cols) * 210, (j // cols) * 373))
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
