#!/usr/bin/env python3
"""Symbolic - KEEP ROLLING (consistency). Split screen, 18 s, loops on itself. Minimal symbolic style.

DAY 1: the same snowy night, the same small snowball in their hands. Above (KEEPS ROLLING): he pushes the same ball
every day; it grows, slowly at first, then faster, until it is taller than he is. Below (STARTS OVER): he pushes a
little, stops - "NEW START." - and makes a new small ball a few steps on; by DAY 30 there is a row of small balls
behind him and none of them grew.  "30 NEW STARTS. / OR ONE THAT KEPT ROLLING."  FOLLOW FOR MORE.
Music: a single music-box note at the start that grows, layer by layer, with the ball.

    python3 stick/snowball.py stick/snowball.mp4
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

T_HOOK = 1.3                # 0-1.3 s: the ending first (DAY 30), then a rewind
T_REW = 1.6
T0, T1 = 1.6, 10.0          # DAY 1 -> DAY 30
R0, R1 = 22, 235
T_L1, T_L2 = 11.0, 12.0
CPS = 18.0
LINE1, LINE2 = "30 NEW STARTS.", "OR ONE THAT KEPT ROLLING."
T_FOLLOW = 12.9
CYCLE = (T1 - T0) / 10      # below: a new start every cycle


def story_t(t):
    """The hook shows the end of the story first."""
    return T1 + 0.8 if t < T_HOOK else t


def day(t):
    return 1 + int(round(29 * prog(t, T0, T1)))


# ---------------------------------------------------------------- poses
STAND = PW.STAND
PUSH = dict(STAND, head=(34, -136), neck=(24, -98), el=(56, -84), hl=(96, -88), er=(50, -78), hr=(90, -82))
HOLD = dict(STAND, el=(30, -76), hl=(52, -86), er=(26, -72), hr=(48, -82))
SHRUG = dict(STAND, head=(0, -150), el=(-36, -76), hl=(-56, -100), er=(36, -76), hr=(56, -100))
LEAN = dict(STAND, head=(16, -148), el=(40, -110), hl=(70, -130), er=(10, -60), hr=(14, -14))
LOOK_BACK = dict(STAND, head=(-6, -150), el=(-16, -60), hl=(-20, -14), er=(16, -60), hr=(20, -14))


def push_pose(t, speed):
    p = AJ.walk(t * speed, PUSH)
    return dict(p, **{j: PUSH[j] for j in ("head", "neck", "el", "hl", "er", "hr")})


def top_state(t):
    """pose, hip, facing, ball (x, r, roll angle)"""
    p = smooth(prog(t, T0, T1))
    g = prog(t, T0, T1) ** 1.7
    r = lerp(R0, R1, g)
    bx = lerp(250, 760, p)
    roll = (bx - 250) / max(r, 1)
    if t < T0:
        return HOLD, (170, STAND_Y), 1, (bx, r, 0)
    if t < T1:
        hip_x = bx - r - 70
        return push_pose(t, 4.5), (hip_x, STAND_Y), 1, (bx, r, roll)
    k = smooth(prog(t, T1, T1 + 0.5))
    return lerp_pose(PUSH, LEAN, k), (bx - r - 60, STAND_Y), 1, (bx, r, roll)


def bottom_state(t):
    """pose, hip, facing, current ball (x, r, roll) or None, left-behind balls [(x, r)]"""
    left = []
    if t < T0:
        return HOLD, (120, STAND_Y), 1, (200, R0, 0), left
    i = min(9, int((t - T0) / CYCLE))
    for j in range(i):
        left.append((200 + j * 70 + 50, R0 + 16))
    u = (t - T0 - i * CYCLE) / CYCLE
    start_x = 200 + i * 70
    if t >= T1:
        left.append((start_x + 50, R0 + 16))
        k = smooth(prog(t, T1, T1 + 0.5))
        return lerp_pose(STAND, LOOK_BACK, k), (start_x + 70, STAND_Y), -1, None, left
    if u < 0.55:
        k = u / 0.55
        r = lerp(R0, R0 + 16, k)
        bx = start_x + 50 * k
        return push_pose(t, 6), (bx - r - 70, STAND_Y), 1, (bx, r, 50 * k / r), left
    if u < 0.8:
        k = math.sin(math.pi * (u - 0.55) / 0.25)
        bx = start_x + 50
        return lerp_pose(STAND, SHRUG, k), (bx - R0 - 16 - 70, STAND_Y), 1, (bx, R0 + 16, 50 / (R0 + 16)), left
    # walks on past the ball he leaves, to start a new one
    k = (u - 0.8) / 0.2
    left.append((start_x + 50, R0 + 16))
    hx = lerp(start_x + 50 - R0 - 16 - 70, start_x + 70 - R0 - 70, k)
    return AJ.walk(t * 7, STAND), (hx, STAND_Y), 1, None, left


# ---------------------------------------------------------------- drawing
def build_bg():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    sky = np.stack([lerp(6, 22, yy / FYP), lerp(8, 26, yy / FYP), lerp(16, 46, yy / FYP)], -1)
    snow = np.stack([200 - (yy - FYP) * 0.1, 206 - (yy - FYP) * 0.1, 220 - (yy - FYP) * 0.08], -1)
    img = np.where((yy < FYP)[..., None], sky, snow)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(3)
    for _ in range(70):
        x, y = rng.uniform(0, W), rng.uniform(70, FYP - 150)
        d.point((x, y), fill=(220, 224, 240, int(rng.uniform(80, 200))))
    # far snowy hills
    pts = [(0, FYP)]
    for x in range(0, W + 40, 40):
        pts.append((x, FYP - 60 - 30 * math.sin(x / 140) - 20 * math.sin(x / 57)))
    pts.append((W, FYP))
    d.polygon(pts, fill=(36, 40, 58, 255))
    d.line([(0, FYP), (W, FYP)], fill=(150, 156, 172, 255), width=2)
    return im


def snowflakes(d, t):
    rng = np.random.default_rng(9)
    for _ in range(45):
        x0, sp, ph = rng.uniform(0, W), rng.uniform(30, 70), rng.uniform(0, PH)
        y = (ph + t * sp) % (FYP + 20)
        x = x0 + 14 * math.sin(t * 0.8 + ph)
        r = rng.uniform(1.5, 3.2)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(240, 244, 255, 200))


def snowball(d, x, r, roll, glow=False):
    ink = INK + (255,)
    cy = FYP - r + 3
    d.ellipse([x - r, cy - r, x + r, cy + r], fill=(240, 244, 250, 255), outline=ink, width=max(3, int(r / 18)))
    # shading on the lower right
    d.chord([x - r * 0.9, cy - r * 0.9, x + r * 0.95, cy + r * 0.95], 300, 120, fill=(212, 218, 232, 255))
    # a few clumps that turn as it rolls
    for j in range(4):
        a = roll + j * math.pi / 2
        px, py = x + 0.55 * r * math.cos(a), cy + 0.55 * r * math.sin(a)
        s = max(2, r * 0.09)
        d.ellipse([px - s, py - s, px + s, py + s], fill=(200, 206, 222, 255))


def trail(d, x0, x1, r):
    if x1 <= x0:
        return
    d.rectangle([x0, FYP - 1, x1, FYP + max(3, r * 0.06)], fill=(150, 158, 178, 255))


def sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    return cv.done()


BG = None
FRAME0 = None


def panel(t, top):
    im = BG.copy()
    d = ImageDraw.Draw(im)
    snowflakes(d, t)
    if top:
        pose, hip, facing, (bx, r, roll) = top_state(t)
        trail(d, 250, bx, r)
        pts = AJ.place(pose, hip, facing, SC)
        spr, off = sprite(pts, FIG, FIG_FAR, facing)
        if t >= T1:
            g = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
            ImageDraw.Draw(g).ellipse([bx - r - 60, FYP - 2 * r - 60, bx + r + 60, FYP + 60], fill=(200, 220, 255, 50))
            im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
            d = ImageDraw.Draw(im)
        if t < T0:
            im.alpha_composite(spr, off)
            d = ImageDraw.Draw(im)
            hx, hy = pts["hl"]
            snowball(d, hx + 10, R0, 0)
        else:
            snowball(d, bx, r, roll)
            im.alpha_composite(PW.glow_of(spr, 0.35, 12), off)
            im.alpha_composite(spr, off)
    else:
        pose, hip, facing, ball, left = bottom_state(t)
        for x, r in left:
            trail(d, x - 50, x, r)
            snowball(d, x, r, 50 / r)
        pts = AJ.place(pose, hip, facing, SC)
        spr, off = sprite(pts, FIG, FIG_FAR, facing)
        if ball is not None:
            bx, r, roll = ball
            if t < T0:
                im.alpha_composite(spr, off)
                d = ImageDraw.Draw(im)
                hx, hy = pts["hl"]
                snowball(d, hx + 10, R0, 0)
            else:
                trail(d, 200 + 70 * min(9, int((t - T0) / CYCLE)), bx, r)
                snowball(d, bx, r, roll)
                im.alpha_composite(spr, off)
        else:
            im.alpha_composite(spr, off)
        d = ImageDraw.Draw(im)
        # "NEW START." the first two times, then just a sigh
        if t >= T0:
            i = min(9, int((t - T0) / CYCLE))
            u = (t - T0 - i * CYCLE) / CYCLE
            if 0.55 <= u < 0.85 and t < T1:
                b0 = T0 + (i + 0.55) * CYCLE
                OC.speech_at(im, t, [(b0, b0 + 0.3 * CYCLE, "NEW START." if i < 3 else "...", "me")], pts)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (2, 2, 4, 255))
    ts = story_t(t)
    img.alpha_composite(panel(ts, True), (0, TOP_Y0))
    img.alpha_composite(panel(ts, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    fl = font(BOLD, 42)
    if t < T_L1:
        spaced(d, W / 2, TOP_Y0 + 24, "KEEPS ROLLING", fl, (250, 250, 252, 255), 12)
    spaced(d, W / 2, BOT_Y0 + 24, "STARTS OVER", fl, (230, 232, 238, 255), 12)
    # the day, small and quiet in the middle
    s = f"DAY {day(ts)}"
    spaced(d, W / 2, STRIP_Y - 26, s, font(BOLD, 44), (220, 226, 240, 255), 8)
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
    if t < T_HOOK:
        # a slow push-in on the ending, so the hook moves from frame 0
        z = 1 + 0.07 * smooth(prog(t, 0, T_HOOK))
        cw, ch = W / z, H / z
        img = img.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
        d = ImageDraw.Draw(img)
    if T_HOOK - 0.05 <= t < T_REW + 0.1:
        k = 1 - abs(prog(t, T_HOOK - 0.05, T_REW + 0.1) * 2 - 1)
        img.alpha_composite(Image.new("RGBA", (W, H), (235, 240, 255, int(235 * k))))
        d = ImageDraw.Draw(img)
        if k > 0.5:
            spaced(d, W / 2, H / 2 - 40, "DAY 1", font(BOLD, 80), (20, 24, 40, 255), 10)
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


def audio():
    """One music-box note that grows, layer by layer, with the ball: box -> + piano -> + pads -> + low strings
    -> a full chord when the ball is complete."""
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    bpm = 96
    beat = 60 / bpm
    bar = 4 * beat
    chords = music.PROG["D"]
    # the hook: the big chord of the ending hits at frame 0, then a rewind sweep
    for k, m in enumerate((38, 50, 57, 62, 66, 69, 74)):
        sig = music.strings(midi(m), 1.2, 0.01, 0.6) if m < 60 else GS.pad(midi(m), 1.2, 0.01, 0.6)
        mix_in(mus, sig, 0.0, 0.06, (k - 3) * 0.25)
    mix_in(mus, tone(36.7, 1.2, (1, 0.5), a=0.003, d=0.6), 0.0, 0.25)
    mix_in(mus, music.music_box(midi(86), 1.4), 0.0, 0.07, 0.2)
    mix_in(fx, tone(2400, 0.32, (1, 0.4), a=0.01, d=0.2, sweep=300) + 0.5 * noise(0.32, 5, lo=500, hi=6000)
           * env(int(0.32 * SR), 0.02, 0.15), T_HOOK, 0.06)
    tt, i = T0, 0
    while tt < T1:
        g = prog(tt, T0, T1) ** 1.6
        ch = chords[int(tt / bar) % 4]
        seq = [0, 1, 2, 1]
        m = ch[seq[i % 4]] + 24
        mix_in(mus, music.music_box(midi(m), 1.4), tt, 0.05 + 0.03 * g, 0.2)
        if g > 0.1:
            mix_in(mus, OC.piano(midi(ch[seq[(i + 2) % 4]] + 12), 0.6, 0.5), tt + beat / 2, 0.06 * g, -0.2)
        i += 1
        tt += beat
    b = 0
    while T0 + b * bar < T1:
        t0 = T0 + b * bar
        g = prog(t0, T0, T1) ** 1.4
        ch = chords[b % 4]
        if g > 0.2:
            for k, m in enumerate(ch):
                mix_in(mus, GS.pad(midi(m), min(bar, T1 - t0), 0.4, 0.8), t0, 0.05 * g, (k - 1) * 0.4)
        if g > 0.45:
            mix_in(mus, music.strings(midi(ch[0] - 12), min(bar, T1 - t0), 0.3, 0.8), t0, 0.06 * g)
            mix_in(mus, music.strings(midi(ch[0] - 24), min(bar, T1 - t0), 0.3, 0.8), t0, 0.05 * g)
        b += 1
    # the ball is complete: a full, warm chord
    for k, m in enumerate((38, 50, 57, 62, 66, 69, 74)):
        sig = music.strings(midi(m), 2.6, 0.08, 1.6) if m < 60 else GS.pad(midi(m), 2.6, 0.08, 1.6)
        mix_in(mus, sig, T1, 0.05, (k - 3) * 0.25)
    mix_in(mus, music.music_box(midi(86), 1.8), T1 + 0.05, 0.06, 0.2)
    # closing notes under the caption
    for j, m in enumerate((81, 78, 74, 69)):
        mix_in(mus, music.music_box(midi(m), 1.6), T_L1 + j * 0.5, 0.05, 0.2)
    for k, m in enumerate((50, 57, 62, 66)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), T_L1 - 0.4, 0.04, (k - 1.5) * 0.4)
    # snow crunching under the boots, and the rolling ball (deeper as it grows)
    for tk in np.arange(T0, T1, 0.33):
        g = prog(tk, T0, T1)
        mix_in(fx, noise(0.09, int(tk * 100), lo=600, hi=5000) * env(int(0.09 * SR), 0.004, 0.04), tk, 0.025, -0.2)
        mix_in(fx, noise(0.3, int(tk * 100) + 1, lo=60 + 0 * g, hi=lerp(1800, 300, g)) * env(int(0.3 * SR), 0.05, 0.15),
               tk, 0.02 + 0.03 * g, -0.3)
    # wind
    w = noise(DUR, 33, lo=200, hi=1200)
    fx[:, 0] += w * 0.006
    fx[:, 1] += np.roll(w, 4000) * 0.006
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
    out = sys.argv[1] if len(sys.argv) > 1 else "snowball.mp4"
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
