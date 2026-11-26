#!/usr/bin/env python3
"""GET UP - a boxing short. ~18.5 s.

HOOK: he's down on the canvas, the referee is counting, the crowd boos.  "GET UP."
Every number of the count cuts to a memory (sepia): laughed at in the gym (4), running at dawn (5), an old taped bag
in a garage (6), someone telling him QUIT (7), his mother (8). At 9 his eyes open. He stands. DOUBT comes in smug -
one uppercut - DOUBT is down. Bell. The referee raises his arm, confetti.
THEY COUNTED HIM OUT. / HE COUNTED ON HIMSELF.

    python3 stick/boxing.py --stills [t ...]   # -> stick/boxing/stills.png
    python3 stick/boxing.py stick/boxing.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import hq  # noqa
import race as R  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import face, outfit, scarf, S, GOLD, RED  # noqa
from money import text, compose, put, track  # noqa

FPS, SR = 30, 44100
DUR = 18.5
NF = int(round(DUR * FPS))
STAND = PW.STAND
HX, DX = 470, 700         # him / DOUBT in the ring
COUNT_T = [0.15, 1.4, 2.6, 3.8, 5.0, 6.2, 7.4, 8.6, 9.8]   # when each number is called (1..9)
FLASH = {4: "gym", 5: "dawn", 6: "garage", 7: "quit", 8: "mom"}
FL_IN, FL_LEN = 0.35, 0.85
T_RISE, T_PUNCH, T_DOWN, T_WIN, T_LINES = 10.0, 13.0, 13.25, 14.6, 16.5
GLOVE_R = (214, 40, 40)
GLOVE_K = (30, 30, 34)
MAT = (214, 214, 222)


def count_at(t):
    n = 0
    for i, c in enumerate(COUNT_T):
        if t >= c:
            n = i + 1
    return n if t < T_RISE else 0


def flash_at(t):
    for n, kind in FLASH.items():
        t0 = COUNT_T[n - 1] + FL_IN
        if t0 <= t < t0 + FL_LEN:
            return kind, t - t0
    return None


# ---------------------------------------------------------------- characters
LYING = {"head": (-150, -10), "neck": (-108, -6), "el": (-80, 30), "hl": (-46, 40), "er": (-80, -44), "hr": (-40, -70),
         "kl": (56, -24), "fl": (113, -2), "kr": (56, -6), "fr": (113, 6)}
GUARD = dict(STAND, el=(26, -70), hl=(40, -130), er=(36, -66), hr=(52, -124))


def boxer_hero(st, p, expr, t, f=1, gloves=True):
    figure(st, p, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(st)
    for side in ("l", "r"):
        line(d, [p["hip"], p["k" + side]], (200, 40, 40, 255), 26 * S)     # red shorts
    face(d, p, expr, f, t)
    scarf(d, p, f)
    if gloves:
        for side in ("hl", "hr"):
            ell(d, *p[side], 19, 17, GLOVE_R + (255,))
            ell(d, p[side][0] - 5, p[side][1] - 6, 6, 4, (250, 120, 120, 255))


def boxer_doubt(st, p, expr, t, f=-1):
    figure(st, p, S * 1.12, light=(0.4, -0.9), body=(205, 208, 216))
    d = ImageDraw.Draw(st)
    outfit(d, p, (34, 34, 40), f, legs=False)
    for side in ("l", "r"):
        line(d, [p["hip"], p["k" + side]], (24, 24, 28, 255), 28 * S)
    face(d, p, expr, f, t)
    for side in ("hl", "hr"):
        ell(d, *p[side], 21, 19, GLOVE_K + (255,))
    hx, hy = p["head"]
    PW.spaced(d, hx * K, (hy - 70) * K, "DOUBT", font("InterDisplay-Bold.otf", 30 * K), (240, 70, 60, 255), 6)


def referee(st, p, t, f=1):
    figure(st, p, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(st)
    outfit(d, p, (236, 236, 240), f, legs=True)
    nx, ny = p["neck"]
    hx_, hy_ = p["hip"]
    for j in range(4):   # stripes
        x = nx - 12 + j * 8
        line(d, [(x, ny + 4), (x + (hx_ - nx) * 0.0, hy_)], (20, 20, 24, 255), 3)
    poly(d, [(nx - 8, ny - 2), (nx, ny + 4), (nx - 8, ny + 10)], (20, 20, 24, 255))
    poly(d, [(nx + 8, ny - 2), (nx, ny + 4), (nx + 8, ny + 10)], (20, 20, 24, 255))
    face(d, p, "determined", f, t)


def plain(st, p, expr, t, f=1, body=(150, 154, 166)):
    figure(st, p, S, light=(0.4, -0.9), body=body)
    face(ImageDraw.Draw(st), p, expr, f, t)


# ---------------------------------------------------------------- the ring
_C = {}


def ring_back(cheer=0.0, t=0.0):
    key = "rb"
    if key not in _C:
        img = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(5)
        for row in range(4):     # crowd silhouettes behind the ropes
            y = FLOOR - 330 + row * 48
            for x in np.arange(-20 + row * 17, W + 40, 44):
                sh = int(28 + row * 8 + rng.uniform(-6, 6))
                ell(d, x, y, 18, 20, (sh, sh, sh + 6, 255))
                rrect(d, (x - 24, y + 14, x + 24, y + 70), 12, (sh, sh, sh + 6, 255))
        _C[key] = img
    img = _C[key].copy()
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(int(t * 9))
    for _ in range(4 + int(10 * cheer)):    # camera flashes
        ell(d, rng.uniform(0, W), rng.uniform(FLOOR - 340, FLOOR - 160), 6, 6, (255, 255, 240, 220))
    return img


def ring(d):
    poly(d, [(0, FLOOR - 4), (W, FLOOR - 4), (W, FLOOR + 30), (0, FLOOR + 30)], MAT + (255,))
    poly(d, [(0, FLOOR + 30), (W, FLOOR + 30), (W, FLOOR + 140), (0, FLOOR + 140)], (120, 24, 30, 255))
    for x in (40, W - 40):
        rrect(d, (x - 12, FLOOR - 250, x + 12, FLOOR), 4, (200, 200, 210, 255))
    for j, col in enumerate(((200, 40, 40), (240, 240, 245), (40, 70, 170))):
        y = FLOOR - 230 + j * 60
        line(d, [(40, y), (W - 40, y + 4)], col + (255,), 7)


def front_ropes(d):
    for j, col in enumerate(((200, 40, 40), (240, 240, 245), (40, 70, 170))):
        y = FLOOR - 170 + j * 70
        line(d, [(-10, y + 40), (W + 10, y + 46)], col + (200,), 5)


# ---------------------------------------------------------------- scenes
def ring_scene(t):
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    ring(d)
    n = count_at(t)
    # him
    if t < T_RISE:
        expr = "determined" if t >= COUNT_T[8] + 0.15 else "tired"
        hp = place(LYING, (HX, FLOOR - 30), 1, S)
        boxer_hero(st, hp, expr, t, 1)
    else:
        rise = smooth(prog(t, T_RISE, T_RISE + 0.9))
        if t < T_PUNCH - 0.5:
            pose = lerp_pose(dict(STAND, head=(30, -100), neck=(20, -70), kl=(40, 20), fl=(0, 60), kr=(-20, 54),
                                  fr=(-60, 60), el=(40, -20), hl=(60, 30), er=(30, -20), hr=(50, 40)), GUARD, rise)
            hy = lerp(FLOOR - 60 * S, FLOOR - 113 * S, rise)
            dodge = smooth(prog(t, 12.2, 12.5)) * (1 - smooth(prog(t, 12.5, 12.8)))
            hp = place(dict(pose, head=(pose["head"][0] - 40 * dodge, pose["head"][1] + 20 * dodge)), (HX - 10 * dodge, hy), 1, S)
        elif t < T_WIN:
            k = smooth(prog(t, T_PUNCH - 0.5, T_PUNCH)) * (1 - smooth(prog(t, T_PUNCH + 0.4, T_PUNCH + 0.9)))
            pose = dict(GUARD, er=(lerp(36, 60, k), lerp(-66, -150, k)), hr=(lerp(52, 110, k), lerp(-124, -200, k)),
                        kl=(lerp(-9, -24, k), 56), fl=(lerp(-13, -40, k), 113))
            hp = place(pose, (HX + 60 * k, FLOOR - 113 * S), 1, S)
        else:
            up = smooth(prog(t, T_WIN, T_WIN + 0.4))
            pose = dict(STAND, er=(lerp(10, 26, up), lerp(-58, -148, up)), hr=(lerp(14, 40, up), lerp(-10, -196, up)))
            hp = place(pose, (HX + 40, FLOOR - 113 * S), 1, S)
        expr = "determined" if t < T_WIN else "happy"
        boxer_hero(st, hp, expr, t, 1)
    # DOUBT
    if t < T_DOWN:
        walk_in = smooth(prog(t, T_RISE + 0.6, 12.0))
        punch = smooth(prog(t, 12.0, 12.3)) * (1 - smooth(prog(t, 12.4, 12.8)))
        pose = dict(GUARD, er=(36 + 30 * punch, -80), hr=(52 + 90 * punch, -120 - 10 * punch))
        dp = place(pose, (lerp(DX + 140, DX, walk_in) - 40 * punch, FLOOR - 113 * S * 1.12), -1, S * 1.12)
        boxer_doubt(st, dp, "smug" if t < T_PUNCH else "shocked", t)
    else:
        fall = smooth(prog(t, T_DOWN, T_DOWN + 0.6))
        dpose = lerp_pose(dict(GUARD, head=(-20, -150)), dict(LYING, head=(150, -10), neck=(108, -6), kl=(-56, -24),
                                                             fl=(-113, -2), kr=(-56, -6), fr=(-113, 6)), fall)
        dp = place(dpose, (DX + 40 * fall, lerp(FLOOR - 113 * S * 1.12, FLOOR - 30, fall)), -1, S * 1.12)
        boxer_doubt(st, dp, "shocked" if fall < 1 else "tired", t)
    # referee
    if t < T_RISE + 0.6:
        call = max([math.sin(math.pi * clamp((t - c) / 0.4)) for c in COUNT_T] + [0])
        rp = place(dict(STAND, head=(20, -128), neck=(12, -94), kl=(30, 14), fl=(-6, 60), kr=(-24, 52), fr=(-60, 60),
                        er=(40, -130 - 30 * call), hr=(50, -180 - 40 * call)), (HX - 230, FLOOR - 70 * S), 1, S)
    elif t < T_WIN:
        rp = place(STAND, (180, FLOOR - 113 * S), 1, S)
    else:   # raises his arm
        rp = place(dict(STAND, er=(30, -150), hr=(50, -196)), (HX - 30, FLOOR - 113 * S), 1, S)
    referee(st, rp, t, 1)
    front_ropes(d)
    # confetti
    if t >= T_WIN:
        rng = np.random.default_rng(1)
        for _ in range(120):
            x0, sp, ph = rng.uniform(0, W), rng.uniform(0.25, 0.5), rng.uniform(0, 1)
            y = ((t - T_WIN) * sp + ph) % 1.0 * (FLOOR + 100) - 60
            c = [(240, 200, 60), (230, 60, 60), (240, 240, 245), (80, 160, 240)][int(ph * 40) % 4]
            rrect(d, (x0 + 20 * math.sin(t * 3 + ph * 9), y, x0 + 20 * math.sin(t * 3 + ph * 9) + 10, y + 6), 1, c + (255,))
    # camera
    if t < 1.4:
        z, cx, cy = 2.4, HX - 80, FLOOR - 90
    elif t < T_RISE:
        z, cx, cy = lerp(2.6, 2.2, (t % 1.2) / 1.2), HX - 60, FLOOR - 70
    elif t < T_PUNCH - 0.5:
        k = smooth(prog(t, T_RISE, T_RISE + 1.0))
        z, cx, cy = lerp(2.2, 2.0, k), lerp(HX - 60, 590, k), lerp(FLOOR - 70, FLOOR - 150, k)
    elif t < T_WIN:
        k = smooth(prog(t, T_PUNCH - 0.2, T_PUNCH + 0.1))
        z, cx, cy = lerp(2.0, 2.4, k), lerp(590, 620, k), lerp(FLOOR - 150, FLOOR - 170, k)
    else:
        k = smooth(prog(t, T_WIN, T_WIN + 1.0))
        z, cx, cy = lerp(2.1, 1.75, k), 520, lerp(FLOOR - 170, FLOOR - 200, k)
    cheer = smooth(prog(t, T_DOWN, T_WIN + 0.5))
    shake = 14 * (1 - (t - T_PUNCH) / 0.35) if T_PUNCH <= t < T_PUNCH + 0.35 else 0
    im = compose(st, None, z, cx + shake * math.sin(t * 90), cy, spots=((HX, 1.0), (DX, 0.6)),
                 back=ring_back(cheer, t), refl=False)
    return im


def memory(kind, u, t):
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    cam = (2.0, 540, FLOOR - 130)
    if kind == "gym":
        line(d, [(640, FLOOR - 480), (640, FLOOR - 330)], (120, 120, 120, 255), 4)
        rrect(d, (612, FLOOR - 330, 668, FLOOR - 150), 20, (110, 60, 50, 255))
        p = place(dict(GUARD, er=(60, -110), hr=(110, -130)), (530, FLOOR - 113 * S), 1, S)
        boxer_hero(st, p, "determined", t)
        for j, x in enumerate((300, 380)):
            pp = place(dict(STAND, er=(40, -110), hr=(90, -120)), (x, FLOOR - 113 * S), 1, S)
            plain(st, pp, "laugh", t)
        cam = (1.7, 470, FLOOR - 150)
    elif kind == "dawn":
        for r, a in ((200, 60), (110, 255)):
            ell(d, 760, FLOOR - 260, r, r, (255, 190, 110, a))
        line(d, [(260, FLOOR), (260, FLOOR - 420)], (60, 60, 70, 255), 7)
        pose = R.run_pose(t * 13, 0.7)
        p = place(pose, R.grounded(pose, 520 + 60 * u, FLOOR, S), 1, S)
        boxer_hero(st, p, "tired", t, gloves=False)
        cam = (1.8, 540, FLOOR - 150)
    elif kind == "garage":
        poly(d, [(200, FLOOR - 520), (880, FLOOR - 520), (880, FLOOR), (200, FLOOR)], (60, 56, 52, 255))
        line(d, [(640, FLOOR - 520), (640, FLOOR - 340)], (160, 150, 120, 255), 3)
        sw = 0.08 * math.sin(t * 7)
        rrect(d, (612, FLOOR - 340, 668, FLOOR - 160), 18, (90, 80, 70, 255))
        for j in range(3):
            line(d, [(612, FLOOR - 300 + j * 50), (668, FLOOR - 290 + j * 50)], (200, 200, 190, 255), 6)
        hit = abs(math.sin(t * 9))
        p = place(dict(GUARD, er=(40 + 50 * hit, -100), hr=(60 + 70 * hit, -120)), (520, FLOOR - 113 * S), 1, S)
        boxer_hero(st, p, "determined", t)
        cam = (1.9, 560, FLOOR - 160)
    elif kind == "quit":
        p = place(dict(STAND, head=(16, -136)), (560, FLOOR - 113 * S), -1, S)
        boxer_hero(st, p, "sad", t, f=-1, gloves=False)
        pp = place(dict(STAND, er=(40, -100), hr=(80, -110)), (400, FLOOR - 113 * S), 1, S)
        plain(st, pp, "smug", t)
        R.bubble(st, u, 0.0, 1.0, "QUIT.", 440, FLOOR - 300, size=40)
        cam = (2.0, 480, FLOOR - 160)
    else:   # mom
        p = place(dict(STAND, head=(10, -140)), (560, FLOOR - 113 * S), -1, S)
        boxer_hero(st, p, "sad" if u < 0.4 else "happy", t, f=-1, gloves=False)
        mp = place(dict(STAND, er=(50, -110), hr=(110, -120), el=(46, -90), hl=(100, -80)), (440, FLOOR - 113 * S * 0.95), 1,
                   S * 0.95)
        figure(st, mp, S * 0.95, light=(0.4, -0.9))
        dd = ImageDraw.Draw(st)
        hx, hy = mp["head"]
        ell(dd, hx - 6, hy - 24, 18, 14, (150, 150, 156, 255))     # grey bun
        outfit(dd, mp, (120, 90, 140), 1, legs=False)
        face(dd, mp, "happy", 1, t)
        cam = (2.0, 500, FLOOR - 170)
    im = compose(st, None, *cam, spots=((540, 1.0),), refl=False)
    # memory look: warm sepia + vignette + grain
    g = ImageOps.grayscale(im.convert("RGB"))
    sep = ImageOps.colorize(g, (30, 18, 8), (250, 220, 170))
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse((-200, -100, W + 200, H + 100), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    out = Image.composite(sep, Image.new("RGB", (W, H), (10, 6, 2)), vig)
    return out.convert("RGBA")


def frame(t):
    fl = flash_at(t)
    if fl:
        im = memory(fl[0], fl[1], t)
    else:
        im = ring_scene(t)
    d = ImageDraw.Draw(im)
    n = count_at(t)
    if n and not fl:
        c = COUNT_T[n - 1]
        k = hq.pop(t, c, 0.18)
        f = font("InterDisplay-Bold.otf", int(260 * max(0.3, k)))
        PW.spaced(d, W / 2, 180, str(n), f, (255, 255, 255, 255), 0)
    if t < 1.4:
        a = hq.pop(t, 0.5, 0.2) if t >= 0.5 else 0
        if a > 0:
            text(im, W / 2, 1420, "GET UP.", int(150 * max(0.3, a)), col=GOLD)
    if 9.8 <= t < T_RISE + 0.9:
        a = hq.pop(t, COUNT_T[8] + 0.1, 0.2)
        text(im, W / 2, 1420, "GET UP.", 150, col=GOLD, a=min(1, a))
    for j, s_ in enumerate(("THEY COUNTED HIM OUT.", "HE COUNTED ON HIMSELF.")):
        a = smooth(prog(t, T_LINES + 0.7 * j, T_LINES + 0.7 * j + 0.35))
        if a > 0:
            text(im, W / 2, 150 + j * 84, s_, 64, col=(GOLD if j else (246, 240, 226)), a=a)
    if fl and fl[1] < 0.06 or (not fl and any(COUNT_T[m - 1] + FL_IN + FL_LEN <= t < COUNT_T[m - 1] + FL_IN + FL_LEN + 0.06
                                                for m in FLASH)):
        im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), 0.45).convert("RGBA")
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


MUSIC = "The Escalation.mp3"
HIT = 308.0


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    put(out, track(MUSIC, HIT - T_LINES, DUR), 0.0, 1.6, fin=0.05, fout=1.0)
    crowd = noise(DUR, 2, lo=200, hi=2500)[:n]
    crowd = np.pad(crowd, (0, n - len(crowd)))
    tt = np.arange(n) / SR
    lvl = 0.05 + 0.12 * np.clip((tt - T_DOWN) / 0.5, 0, 1) * np.clip((DUR - tt) / 2, 0, 1)
    out += (crowd * lvl)[:, None]
    for c in COUNT_T:     # the count: a hard clap + boom
        mix_in(out, noise(0.12, 5, lo=800, hi=6000)[:int(0.12 * SR)] * env(int(0.12 * SR), 0.001, 0.08), c, 0.4, 0.0)
        mix_in(out, tone(70, 0.4, (1, 2), a=0.002, d=0.3), c, 0.45, 0.0)
    for m in FLASH:
        mix_in(out, noise(0.3, 7, lo=400, hi=6000)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.15, 0.1), COUNT_T[m - 1] + FL_IN - 0.15,
               0.15, 0.0)
    mix_in(out, noise(0.3, 9, lo=40, hi=900)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.002, 0.2), T_PUNCH, 0.9, 0.2)
    mix_in(out, tone(50, 0.7, (1, 2), a=0.002, d=0.6), T_PUNCH, 0.7, 0.0)
    mix_in(out, tone(1250, 1.4, (1, 2.7, 4.2), a=0.001, d=1.3), T_WIN, 0.35, 0.0)     # the bell
    out *= np.clip((DUR - tt) / 0.6, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "boxing"), exist_ok=True)
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [0.8, 4.5, 5.7, 6.9, 8.1, 9.3, 10.3, 12.2, 13.4, 17.8]
        sheet = Image.new("RGB", (360 * len(ts), 640))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS), (j * 360, 0))
        p = os.path.join(here, "boxing", "stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "boxing.mp4")
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
