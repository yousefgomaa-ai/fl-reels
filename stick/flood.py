#!/usr/bin/env python3
"""THE FLOOD - Victim vs Fighter vs Builder: who rises?  26 s.

Night, rain, a street filling with water. Crates float in, each one a problem (REJECTED, BROKE, FAILED, ...).
THE VICTIM hugs one and cries while the water climbs to his chin. THE FIGHTER smashes every crate until he's too
tired to swim. THE BUILDER (red scarf) stacks them and climbs. Re-hook: a huge BETRAYED crate knocks him under -
"HE WENT UNDER..." - he comes back up and makes it the top step. Dawn. He reaches down and pulls the victim up.
THEY THREW IT AT HIM. / HE STOOD ON IT.

    python3 stick/flood.py --stills [t ...]   # -> stick/flood/stills.png
    python3 stick/flood.py stick/flood.mp4
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
from money_chars import hero, face, S, GOLD, RED  # noqa
from money import text, compose, put, track, rain  # noqa

FPS, SR = 30, 44100
HOOK, DUR = 1.3, 26.0
NF = int(round(DUR * FPS))
STAND = PW.STAND
LX = [300, 540, 780]
CW, CH = 84, 58
WOOD = (150, 108, 64)
WOOD_D = (96, 66, 38)
ORANGE = (240, 130, 40)
VBODY = (178, 188, 206)
B_TIMES = [3.0, 4.6, 6.2, 7.8, 9.4, 11.0, 12.6]
B_LABELS = ["REJECTED", "BROKE", "FAILED", "ALONE", "DEBT", "SICK", "LAID OFF"]
F_TIMES = [3.6, 5.4, 7.2, 9.0, 10.8, 12.6]
F_LABELS = ["REJECTED", "BROKE", "FAILED", "DEBT", "ALONE", "SICK"]
T_BIG, T_UP, T_PLACE = 14.2, 15.6, 16.6
T_DRIFT, T_PULL, T_LINES = 18.6, 20.4, 23.0
DRIFT = 0.9      # seconds a crate floats in


def wl(t):
    """water level (world y)"""
    return FLOOR - 20 - 420 * smooth(prog(t, 1.3, 20.0))


def dawn(t):
    return smooth(prog(t, 19.0, 23.0))


# ---------------------------------------------------------------- props
def crate(d, x, y, label, w=CW, h=CH, rot=0.0, big=False):
    """x, y = centre"""
    c_, s_ = math.cos(rot), math.sin(rot)

    def P(px, py):
        return (x + px * c_ - py * s_, y + px * s_ + py * c_)
    poly(d, [P(-w / 2, -h / 2), P(w / 2, -h / 2), P(w / 2, h / 2), P(-w / 2, h / 2)], WOOD + (255,),
         outline=WOOD_D + (255,), w=3)
    for j in (-1, 1):
        line(d, [P(-w / 2 + 4, j * h / 4), P(w / 2 - 4, j * h / 4)], WOOD_D + (255,), 2)
    line(d, [P(-w / 2 + 4, -h / 2 + 4), P(w / 2 - 4, h / 2 - 4)], WOOD_D + (255,), 3)
    if label:
        fs = (26 if big else 15) * K
        tmp = Image.new("RGBA", (int(w * K), int(h * K)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.rounded_rectangle((4 * K, h * K * 0.28, w * K - 4 * K, h * K * 0.72), 4 * K, fill=(236, 226, 200, 255))
        td.text((w * K / 2, h * K / 2), label, font=font("InterDisplay-Bold.otf", int(fs)), fill=(170, 30, 30, 255),
                anchor="mm")
        tmp = tmp.rotate(-math.degrees(rot), resample=Image.BICUBIC, expand=True)
        d._image.alpha_composite(tmp, (int(x * K - tmp.size[0] / 2), int(y * K - tmp.size[1] / 2)))


def plank(d, x, y, rot):
    c_, s_ = math.cos(rot), math.sin(rot)
    pts = [(-30, -6), (30, -6), (30, 6), (-30, 6)]
    poly(d, [(x + px * c_ - py * s_, y + px * s_ + py * c_) for px, py in pts], WOOD + (255,), outline=WOOD_D + (255,), w=2)


def float_in(t, t0, side, lane_x):
    """position of a crate floating in from the side and arriving at the lane at t0+DRIFT"""
    u = smooth(clamp((t - t0) / DRIFT))
    x0 = lane_x + side * 360
    bob = 4 * math.sin(t * 4 + t0)
    return lerp(x0, lane_x + side * 70, u), wl(t) - 14 + bob


# ---------------------------------------------------------------- characters
def fighter(st, pts, expr, t, gloves=True):
    figure(st, pts, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(st)
    hx, hy = pts["head"]
    line(d, [(hx - 29, hy - 10), (hx + 29, hy - 12)], ORANGE + (255,), 7)
    line(d, [(hx - 26, hy - 10), (hx - 44, hy + 6)], ORANGE + (255,), 5)
    face(d, pts, expr, 1, t)
    if gloves:
        for side in ("hl", "hr"):
            ell(d, *pts[side], 15, 13, (200, 50, 40, 255))


def victim(st, pts, expr, t, f=1):
    figure(st, pts, S, light=(0.4, -0.9), body=VBODY)
    face(ImageDraw.Draw(st), pts, expr, f, t)


def builder(st, pts, expr, t, f=1):
    hero(st, pts, "plain", f, expr, t)


# ---------------------------------------------------------------- the scene
def stack_count(t):
    return sum(1 for tb in B_TIMES if t >= tb + DRIFT + 0.35)


def stack_top(t):
    n = stack_count(t)
    top = FLOOR - n * CH
    if t >= T_PLACE + 0.6:
        top -= 80
    return top


def frame_world(t):
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    w_ = wl(t)
    BX = LX[2]       # the builder's lane (right)
    FX = LX[1]       # fighter (middle)
    VX = LX[0]       # victim (left)
    # ---------------- builder: stacked crates
    n = stack_count(t)
    for j in range(n):
        crate(d, BX + (6 if j % 2 else -6), FLOOR - CH / 2 - j * CH, B_LABELS[j])
    if t >= T_PLACE + 0.6:
        crate(d, BX, FLOOR - n * CH - 40, "BETRAYED", w=130, h=80, big=True)
    # crates on their way to him
    for j, tb in enumerate(B_TIMES):
        if tb <= t < tb + DRIFT + 0.35:
            if t < tb + DRIFT:
                x, y = float_in(t, tb, 1, BX)
            else:   # lifted onto the stack
                k = smooth(prog(t, tb + DRIFT, tb + DRIFT + 0.35))
                x = lerp(BX + 70, BX + (6 if j % 2 else -6), k)
                y = lerp(w_ - 14, FLOOR - CH / 2 - j * CH - 30 * math.sin(math.pi * k), k)
            crate(d, x, y, B_LABELS[j])
    # the big one
    if T_BIG - 0.6 <= t < T_PLACE + 0.6:
        if t < T_BIG:
            y = lerp(-200, stack_top(t) - 120, ((t - (T_BIG - 0.6)) / 0.6) ** 2)
            crate(d, BX + 10, y, "BETRAYED", w=130, h=80, big=True)
        elif t < T_PLACE:
            crate(d, BX + 96, w_ - 20 + 5 * math.sin(t * 3), "BETRAYED", w=130, h=80, big=True, rot=0.15)
        else:
            k = smooth(prog(t, T_PLACE, T_PLACE + 0.6))
            crate(d, lerp(BX + 96, BX, k), lerp(w_ - 20, FLOOR - n * CH - 40 - 40 * math.sin(math.pi * k), k), "BETRAYED",
                  w=130, h=80, big=True, rot=lerp(0.15, 0, k))
    # builder himself
    top = stack_top(t)
    bexpr = "determined"
    if T_BIG <= t < T_UP:            # knocked off, under water
        bp = None
    elif T_UP <= t < T_PLACE + 0.6:  # back up, pushing the big crate
        k = smooth(prog(t, T_UP, T_UP + 0.6))
        bp = place(dict(STAND, er=(40, -110), hr=(80, -120)), (BX + 44, lerp(w_ + 120, top - 113 * S, k)), -1, S)
        bexpr = "determined"
    else:
        lifting = any(tb + DRIFT - 0.1 <= t < tb + DRIFT + 0.35 for tb in B_TIMES)
        pose = dict(PW.ARMS_UP) if lifting else dict(STAND)
        if t >= T_PULL:              # kneels and pulls the victim up
            k = smooth(prog(t, T_PULL, T_PULL + 0.5))
            pose = lerp_pose(STAND, dict(STAND, head=(30, -120), neck=(20, -84), kl=(30, 20), fl=(-10, 60), kr=(-20, 54),
                                         fr=(-60, 60), er=(60, -40), hr=(70, 30)), k * (1 - smooth(prog(t, 21.6, 22.2))))
            bexpr = "happy" if t >= 21.4 else "determined"
        bp = place(pose, (BX + (24 if t >= T_PULL else 0), top - 113 * S), -1 if t >= T_PULL else 1, S)
        if t >= 19.0 and t < T_PULL:
            bexpr = "happy"
    if bp is not None:
        builder(st, bp, bexpr, t, f=-1 if t >= T_PULL or (T_UP <= t < T_PLACE + 0.6) else 1)
    # ---------------- fighter: punches every crate
    tired = smooth(prog(t, 13.5, 16.0))
    bob = 6 * math.sin(t * 5)
    hip_y = min(FLOOR - 113 * S, w_ + 120 + bob)
    punch = 0.0
    for tf in F_TIMES:
        if tf + DRIFT - 0.15 <= t < tf + DRIFT + 0.25:
            punch = math.sin(math.pi * clamp((t - (tf + DRIFT - 0.15)) / 0.4))
    pose = dict(STAND, er=(30 + 30 * punch, -100 - 10 * punch), hr=(40 + 80 * punch, -110 - 20 * punch),
                el=(-10, -90), hl=(10, -120))
    if tired > 0:
        pose = lerp_pose(pose, dict(STAND, head=(10, -144), el=(30, -70), hl=(60, -96), er=(36, -68), hr=(66, -92)), tired)
    fp = place(pose, (FX - 40, hip_y), 1, S)
    fexpr = "angry" if tired < 0.5 else "tired"
    for j, tf in enumerate(F_TIMES):
        if tf <= t < tf + DRIFT:
            x, y = float_in(t, tf, 1, FX - 40)
            crate(d, x, y, F_LABELS[j])
        elif t >= tf + DRIFT:   # smashed: planks drift away
            v = t - tf - DRIFT
            for k_ in range(3):
                a = (k_ - 1) * 0.9 + 0.3
                px = FX + 30 + 60 * v * math.cos(a) + k_ * 10
                if px < W + 60:
                    plank(d, px, w_ - 8 + 3 * math.sin(t * 4 + k_), 0.4 * k_ + v)
    if t >= 15.0:   # holds a plank, exhausted
        plank(d, fp["hr"][0] + 6, fp["hr"][1] + 6, 0.1)
    fighter(st, fp, fexpr, t)
    # ---------------- victim: hugs one crate and waits
    vx = VX
    if t >= T_DRIFT:
        vx = lerp(VX, BX - 120, smooth(prog(t, T_DRIFT, T_PULL)))
    pulled = smooth(prog(t, T_PULL + 0.4, 21.6))
    v_hip = min(FLOOR - 113 * S, w_ + 110 + 4 * math.sin(t * 3))
    if pulled > 0:
        v_hip = lerp(v_hip, top - 113 * S, pulled)
        vx = lerp(vx, BX - 60, pulled)
    vpose = dict(STAND, el=(26, -80), hl=(54, -60), er=(30, -76), hr=(58, -56), head=(6, -148))
    if pulled > 0:
        vpose = lerp_pose(vpose, dict(STAND, er=(40, -130), hr=(70, -160)), pulled)
    vp = place(vpose, (vx, v_hip), 1, S)
    vexpr = "sad" if t < 7.0 else "cry"
    if pulled > 0.5:
        vexpr = "happy"
    if pulled < 0.5:
        crate(d, vp["hr"][0] + 10, vp["hr"][1] + 14, "ALONE", rot=-0.1)
    victim(st, vp, vexpr, t)
    if T_PULL <= t < 21.6 and bp is not None:     # the hands meet
        line(d, [bp["hr"], vp["hr"]], (238, 238, 242, 255), 9)
    return st


def water_layer(t):
    w_ = wl(t)
    lay = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dw = dawn(t)
    top_col = (int(lerp(40, 90, dw)), int(lerp(90, 110, dw)), int(lerp(140, 130, dw)))
    for j in range(24):
        y0 = w_ + j * 40
        k = j / 23
        col = tuple(int(c * (1 - 0.55 * k)) for c in top_col)
        d.rectangle((0, y0 * K, W * K, (y0 + 40) * K), col + (int(lerp(150, 235, k)),))
    pts = [(x, w_ + 5 * math.sin(x / 50 + t * 3) + 3 * math.sin(x / 23 - t * 5)) for x in range(-10, W + 20, 20)]
    line(d, pts, (int(lerp(170, 255, dw)), int(lerp(210, 220, dw)), int(lerp(250, 170, dw)), 230), 3)
    rng = np.random.default_rng(int(t * 12))
    for _ in range(18):
        x = rng.uniform(0, W)
        ell(d, x, w_ + rng.uniform(4, 40), rng.uniform(8, 26), 2, (200, 220, 255, 60))
    return lay


def sky(t):
    dw = dawn(t)
    img = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    if dw <= 0:
        return img
    d = ImageDraw.Draw(img)
    for j in range(40):
        y = j * 40
        k = j / 39
        a = int(dw * 255 * (0.25 + 0.75 * k))
        d.rectangle((0, y * K, W * K, (y + 40) * K), (int(lerp(30, 255, k)), int(lerp(30, 150, k)), int(lerp(70, 80, k)), a))
    sy = lerp(1100, 760, dw)
    for r, a in ((240, 40), (160, 80), (90, 255)):
        d.ellipse(((700 - r) * K, (sy - r) * K, (700 + r) * K, (sy + r) * K), (255, 214, 130, int(a * dw)))
    return img


def skyline():
    img = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(3)
    x = 0
    while x < W:
        w = rng.uniform(60, 130)
        h = rng.uniform(200, 520)
        poly(d, [(x, FLOOR - h), (x + w, FLOOR - h), (x + w, FLOOR), (x, FLOOR)], (14, 16, 24, 255))
        for yy in np.arange(FLOOR - h + 14, FLOOR - 10, 22):
            for xx in np.arange(x + 8, x + w - 8, 16):
                if rng.uniform() < 0.18:
                    rrect(d, (xx, yy, xx + 7, yy + 10), 1, (230, 190, 110, 150))
        x += w + rng.uniform(4, 20)
    return img


_SK = {}


def frame(t):
    s = t
    hook = t < HOOK
    if hook:
        s = 6.6 + min(t, 0.8) * 1.0
    st = frame_world(s)
    d = ImageDraw.Draw(st)
    if not hook and t < 19.5:
        rain(d, t, 1.0 - smooth(prog(t, 18.0, 19.5)), seed=6, n=140)
    if "sk" not in _SK:
        _SK["sk"] = skyline()
    back = sky(s).copy()
    back.alpha_composite(_SK["sk"])
    bd = ImageDraw.Draw(back)
    bd.rectangle((0, wl(s) * K, W * K, H * K), (14, 30, 52, 255))
    st.alpha_composite(water_layer(s))
    if T_BIG <= s < T_BIG + 0.7:   # the splash
        u = (s - T_BIG) / 0.7
        rng = np.random.default_rng(2)
        for _ in range(30):
            a = rng.uniform(math.pi * 1.1, math.pi * 1.9)
            r = 260 * u * rng.uniform(0.5, 1.0)
            ell(d, LX[2] + r * math.cos(a), wl(s) + r * math.sin(a) + 300 * u * u, 6, 6, (210, 230, 255, int(220 * (1 - u))))
    Z = 1.6
    cy = wl(s) - 150
    shake = 12 * (1 - (s - T_BIG) / 0.5) if T_BIG <= s < T_BIG + 0.5 else 0
    im = compose(st, None, Z, W / 2 + shake * math.sin(t * 80), cy, spots=((LX[0], 0.6), (LX[1], 0.6), (LX[2], 0.9)),
                 back=back, refl=False)
    dd = ImageDraw.Draw(im)
    # lane names
    if not s >= T_LINES - 0.5:
        a = 1 - smooth(prog(s, T_LINES - 1.0, T_LINES - 0.5))
        for x, lab, col in ((LX[0], "VICTIM", (160, 176, 210)), (LX[1], "FIGHTER", ORANGE), (LX[2], "BUILDER", (236, 70, 60))):
            PW.spaced(dd, (x - W / 2) * Z + W / 2, 150, lab, font("InterDisplay-Bold.otf", 40), col + (int(255 * a),), 5)
        PW.spaced(dd, W / 2, 50, "WHO RISES?", font("InterDisplay-Bold.otf", 64), (246, 246, 250, int(255 * a)), 6)
    if hook and t >= 0.8:
        im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (0, 0, 0)), 0.35).convert("RGBA")
        k = hq.pop(t, 0.8, 0.2)
        text(im, W / 2, 380, "ONLY ONE WILL", int(92 * max(0.3, k)))
        text(im, W / 2, 380 + int(104 * max(0.3, k)), "STAND ABOVE IT.", int(92 * max(0.3, k)), col=GOLD)
    if 14.5 <= t < 15.9:
        a = hq.pop(t, 14.5, 0.25) * (1 - smooth(prog(t, 15.6, 15.9)))
        text(im, W / 2, 420, "HE WENT UNDER...", 84, a=min(1, a))
    for j, s_ in enumerate(("THEY THREW IT AT HIM.", "HE STOOD ON IT.")):
        a = smooth(prog(t, T_LINES + 0.8 * j, T_LINES + 0.8 * j + 0.4))
        if a > 0:
            text(im, W / 2, 120 + j * 86, s_, 66, col=(GOLD if j else (246, 240, 226)), a=a)
    if HOOK <= t < HOOK + 0.1:
        im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), 0.6 * (1 - (t - HOOK) / 0.1))
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


MUSIC = "Undaunted.mp3"
HIT = 69.0     # the track's big lift -> the end lines


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    put(out, track(MUSIC, HIT - T_LINES, DUR), 0.0, 1.8, fin=0.05, fout=1.0)
    rainn = noise(DUR, 3, lo=800, hi=9000)[:n]
    rainn = np.pad(rainn, (0, n - len(rainn)))
    out += (rainn * np.clip(1 - (np.arange(n) / SR - 18.0) / 1.5, 0, 1) * 0.05)[:, None]
    for tb in B_TIMES:
        mix_in(out, tone(110, 0.15, (1, 2.2), a=0.002, d=0.1), tb + DRIFT + 0.35, 0.35, 0.5)
    for tf in F_TIMES:
        mix_in(out, noise(0.2, 6, lo=60, hi=1500)[:int(0.2 * SR)] * env(int(0.2 * SR), 0.002, 0.12), tf + DRIFT, 0.45, 0.0)
    splash = noise(1.2, 8, lo=200, hi=6000)[:int(1.2 * SR)] * env(int(1.2 * SR), 0.005, 0.8)
    mix_in(out, splash, T_BIG, 0.55, 0.4)
    mix_in(out, tone(55, 0.8, (1, 2), a=0.002, d=0.7), T_BIG, 0.5, 0.0)
    mix_in(out, noise(0.5, 3, lo=40, hi=1800)[:int(0.5 * SR)] * env(int(0.5 * SR), 0.003, 0.35), 0.8, 0.45, 0.0)
    rew = noise(0.35, 9, lo=500, hi=7000)[:int(0.35 * SR)] * env(int(0.35 * SR), 0.25, 0.05)
    mix_in(out, rew, HOOK - 0.3, 0.2, 0.0)
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.8, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "flood"), exist_ok=True)
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [1.0, 5.0, 10.0, 14.7, 17.2, 21.0, 24.5]
        sheet = Image.new("RGB", (360 * len(ts), 640))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS), (j * 360, 0))
        p = os.path.join(here, "flood", "stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "flood.mp4")
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
