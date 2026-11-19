#!/usr/bin/env python3
"""IDEAS.md #3 - 1% BATTERY vs 80% BATTERY. Split screen, the channel's current style, 18 s, loops on itself.

Same night, same bench under the same street lamp. Above, at 1%: "I'M AT 1%." Below, at 80%: "80%. I'M FINE."
The red clock runs 21:00 -> 01:58. Both take a selfie (flash), video-call, play a game. Above, the battery blinks
"1%" all night. Below, it drops: 80, 64, 41, 18, 6. At 01:58 both open the taxi app; below, "BOOKING YOUR RIDE..." -
the screen goes black: 0%. "NO. NO. NO." Above, a taxi pulls up, he gets in, still at 1%, and is gone.
"1% LASTS LONGER. / NOBODY KNOWS WHY."  FOLLOW FOR MORE.

    python3 stick/battery.py stick/battery.mp4
    ONLY_FRAMES=0.5,2.7,5.3,8.3,11.0,12.4,13.2,14.0,15.0,17.4 python3 stick/battery.py /tmp/bt
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
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back, out_cubic,  # noqa
                          prog, rot, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 7.5 * BAR
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
LOW, LOW_FAR = AJ.DOER, AJ.DOER_FAR      # the 1% one (he wins)
HIGH, HIGH_FAR = AJ.OT, AJ.OT_FAR
RED, GREEN, YELLOW = (255, 64, 56), (90, 230, 130), (250, 210, 70)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 113 * SC
BENCH_X = 380
LAMP_X = 250
HIP_SIT = (BENCH_X, FYP - 115 * SC)

# ---------------------------------------------------------------- timeline
T_CLOCK0, T_CLOCK1 = 1.8, 12.0          # 21:00 -> 01:58
T_SELFIE0, T_SELFIE1 = 2.4, 3.6
T_CALL0, T_CALL1 = 4.6, 6.6
T_GAME0, T_GAME1 = 7.6, 10.4
T_TAXI0 = 11.6                           # both open the taxi app
T_DEAD = 12.85
T_CAR0, T_CAR1 = 12.4, 13.3              # the taxi pulls up above
T_GETIN0, T_GETIN1 = 13.4, 13.9
T_CAROUT0, T_CAROUT1 = 14.0, 14.9
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "1% LASTS LONGER.", "NOBODY KNOWS WHY."
T_FOLLOW = 16.95

BUB_LOW = [(0.3, 1.6, "I'M AT 1%.", "me"), (5.0, 6.2, "HI MOM! NO, IT'S FINE.", "me"), (11.65, 12.4, "TAXI TIME.", "me")]
BUB_HIGH = [(1.0, 2.3, "80%. I'M FINE.", "me"), (11.65, 12.4, "TAXI TIME.", "me"), (13.0, 14.6, "NO. NO. NO.", "me")]
DROPS = [(0.0, 80), (3.2, 64), (6.0, 41), (9.0, 18), (11.0, 6), (T_DEAD, 0)]


def clock_minutes(t):
    return int(21 * 60 + 298 * prog(t, T_CLOCK0, T_CLOCK1) ** 1.1) % 1440


def battery(t, low):
    if low:
        return 1
    v = 80
    for t0, p in DROPS:
        if t >= t0:
            v = p
    return v


# ---------------------------------------------------------------- poses
SIT = OC.SIT
SIT_PHONE = OC.SIT_PHONE
SELFIE = dict(AJ.SIT_TYPE, el=(40, -150), hl=(76, -196), er=(26, -56), hr=(50, -12))
CALL = OC.CALL
GAME = dict(AJ.SIT_TYPE, head=(16, -144), neck=(10, -102), el=(30, -66), hl=(50, -96), er=(40, -62), hr=(74, -92))
STAND = PW.STAND
STAND_PHONE = dict(STAND, el=(26, -66), hl=(44, -100), er=(22, -62), hr=(40, -96))
WAVE = dict(STAND, er=(36, -140), hr=(56, -186))
HOLD_HEAD = dict(STAND, el=(-34, -146), hl=(-10, -176), er=(34, -146), hr=(10, -176))


def person(t, low):
    """(pose, x, y, facing, prop, alpha)"""
    if t < T_SELFIE0:
        return SIT_PHONE, HIP_SIT[0], HIP_SIT[1], 1, "phone", 1.0
    if t < T_SELFIE1:
        return SELFIE, HIP_SIT[0], HIP_SIT[1], 1, "selfie", 1.0
    if t < T_CALL0:
        return SIT_PHONE, HIP_SIT[0], HIP_SIT[1], 1, "phone", 1.0
    if t < T_CALL1:
        return CALL, HIP_SIT[0], HIP_SIT[1], 1, "call", 1.0
    if t < T_GAME0:
        return SIT_PHONE, HIP_SIT[0], HIP_SIT[1], 1, "phone", 1.0
    if t < T_GAME1:
        p = dict(GAME)
        j = 4 * math.sin(t * 18)
        p["hl"] = (p["hl"][0], p["hl"][1] - abs(j))
        p["hr"] = (p["hr"][0], p["hr"][1] - abs(math.cos(t * 16)) * 4)
        return p, HIP_SIT[0], HIP_SIT[1], 1, "game", 1.0
    if t < T_TAXI0:
        k = smooth(prog(t, T_GAME1, T_TAXI0))
        return lerp_pose(SIT_PHONE, STAND_PHONE, k), HIP_SIT[0] + 40 * k, lerp(HIP_SIT[1], STAND_Y, k), 1, "phone", 1.0
    if low:
        if t < T_GETIN0:
            p = WAVE if t >= T_CAR1 else STAND_PHONE
            return p, HIP_SIT[0] + 40, STAND_Y, 1, "taxi" if t < T_CAR1 else None, 1.0
        if t < T_GETIN1:
            x = lerp(HIP_SIT[0] + 40, 640, smooth(prog(t, T_GETIN0, T_GETIN1)))
            return AJ.walk(t * 8, STAND), x, STAND_Y, 1, None, 1 - smooth(prog(t, T_GETIN1 - 0.2, T_GETIN1))
        return STAND, -900, STAND_Y, 1, None, 0.0
    if t < T_DEAD + 0.2:
        return STAND_PHONE, HIP_SIT[0] + 40, STAND_Y, 1, "taxi", 1.0
    k = smooth(prog(t, T_DEAD + 0.2, T_DEAD + 0.5))
    return lerp_pose(STAND_PHONE, HOLD_HEAD, k), HIP_SIT[0] + 40, STAND_Y, 1, "dead" if k < 0.5 else None, 1.0


# ---------------------------------------------------------------- the street
def build_street():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    g = np.clip(yy / FYP, 0, 1)[..., None]
    img = (1 - g) * np.array([8, 10, 22], np.float32) + g * np.array([18, 22, 40], np.float32)
    lamp = np.exp(-(((xx - LAMP_X - 30) / 260) ** 2 + ((yy - FYP) / 140) ** 2)) * 70
    img += lamp[..., None] * np.array([1.0, 0.85, 0.55], np.float32)
    inside = (yy > 150) & (yy < FYP)
    half = 30 + (yy - 150) / (FYP - 150) * 210
    cone = np.where(inside, np.clip(1 - np.abs(xx - LAMP_X - 30) / half, 0, 1) ** 1.5, 0) * 26
    img += cone[..., None] * np.array([1.0, 0.85, 0.55], np.float32)
    img = np.where((yy > FYP)[..., None], np.array([30, 30, 36], np.float32) + lamp[..., None] * 0.4, img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    rng = np.random.default_rng(3)
    # buildings with a few lit windows, stars
    for i in range(30):
        x, y = rng.uniform(0, W), rng.uniform(10, 160)
        d.ellipse([x - 1.2, y - 1.2, x + 1.2, y + 1.2], fill=(200, 200, 220, 255))
    x = 520
    while x < W:
        bw = rng.uniform(90, 150)
        bh = rng.uniform(220, 420)
        d.rectangle([x, FYP - bh, x + bw, FYP], fill=(16, 18, 30, 255))
        for wy in range(int(FYP - bh + 20), int(FYP - 40), 34):
            for wx in range(int(x + 14), int(x + bw - 20), 30):
                if rng.uniform() < 0.25:
                    d.rectangle([wx, wy, wx + 12, wy + 16], fill=(250, 210, 120, 255))
        x += bw + 10
    d.rectangle([0, FYP, W, FYP + 14], fill=(70, 70, 78, 255))
    d.line([(0, FYP), (W, FYP)], fill=(100, 100, 110, 255), width=2)
    for i in range(0, W, 120):
        d.rectangle([i + 30, FYP + 50, i + 90, FYP + 56], fill=(200, 190, 120, 255))
    # the street lamp
    d.rectangle([LAMP_X - 6, 140, LAMP_X + 6, FYP], fill=(60, 60, 66, 255), outline=ink, width=2)
    d.line([(LAMP_X, 146), (LAMP_X + 40, 146)], fill=(60, 60, 66, 255), width=8)
    d.polygon([(LAMP_X + 14, 146), (LAMP_X + 66, 146), (LAMP_X + 56, 166), (LAMP_X + 24, 166)], fill=(60, 60, 66, 255),
              outline=ink)
    d.ellipse([LAMP_X + 28, 160, LAMP_X + 52, 172], fill=(255, 236, 190, 255))
    # the bench
    d.rectangle([BENCH_X - 110, FYP - 128, BENCH_X + 110, FYP - 112], fill=(110, 80, 56, 255), outline=ink, width=3)
    d.rectangle([BENCH_X - 110, FYP - 200, BENCH_X + 110, FYP - 184], fill=(110, 80, 56, 255), outline=ink, width=3)
    for lx in (BENCH_X - 96, BENCH_X + 86):
        d.rectangle([lx, FYP - 112, lx + 10, FYP], fill=(50, 50, 56, 255))
        d.rectangle([lx, FYP - 200, lx + 6, FYP - 128], fill=(50, 50, 56, 255))
    return im


def draw_taxi(d, x):
    ink = INK + (255,)
    y = FYP + 30
    d.rounded_rectangle([x, y - 110, x + 300, y - 30], 18, fill=(250, 200, 50, 255), outline=ink, width=4)
    d.polygon([(x + 60, y - 110), (x + 100, y - 160), (x + 220, y - 160), (x + 250, y - 110)], fill=(250, 200, 50, 255),
              outline=ink)
    d.polygon([(x + 76, y - 112), (x + 106, y - 150), (x + 156, y - 150), (x + 156, y - 112)], fill=(150, 200, 240, 255))
    d.polygon([(x + 166, y - 112), (x + 166, y - 150), (x + 214, y - 150), (x + 236, y - 112)], fill=(150, 200, 240, 255))
    d.rectangle([x + 130, y - 182, x + 190, y - 160], fill=(240, 240, 240, 255), outline=ink, width=3)
    spaced(d, x + 160, y - 180, "TAXI", font("Inter-Bold.otf", 16), (20, 20, 24, 255), 1)
    for wx in (x + 70, x + 236):
        d.ellipse([wx - 30, y - 60, wx + 30, y], fill=(30, 30, 34, 255), outline=ink, width=3)
        d.ellipse([wx - 12, y - 42, wx + 12, y - 18], fill=(150, 150, 160, 255))
    d.ellipse([x + 284, y - 96, x + 300, y - 80], fill=(255, 250, 200, 255))


def phone_screen(d, cx, cy, kind, t):
    """A big phone screen drawn next to the hand when it matters (taxi app / dead)."""
    ink = INK + (255,)
    x0, y0 = cx - 80, cy - 150
    d.rounded_rectangle([x0, y0, x0 + 160, y0 + 290], 18, fill=(24, 26, 34, 255), outline=ink, width=5)
    if kind == "dead":
        d.rectangle([x0 + 10, y0 + 18, x0 + 150, y0 + 272], fill=(4, 4, 6, 255))
        d.rounded_rectangle([x0 + 50, y0 + 130, x0 + 104, y0 + 158], 4, outline=(200, 40, 40, 255), width=3)
        d.rectangle([x0 + 104, y0 + 138, x0 + 110, y0 + 150], fill=(200, 40, 40, 255))
        return
    d.rectangle([x0 + 10, y0 + 18, x0 + 150, y0 + 272], fill=(210, 220, 230, 255))
    for i in range(6):
        d.line([(x0 + 10, y0 + 40 + i * 40), (x0 + 150, y0 + 30 + i * 44)], fill=(240, 244, 248, 255), width=6)
    d.ellipse([x0 + 70, y0 + 120, x0 + 90, y0 + 140], fill=RED + (255,))
    d.rectangle([x0 + 20, y0 + 220, x0 + 140, y0 + 260], fill=(30, 30, 36, 255))
    dots = "." * (1 + int(t * 3) % 3)
    spaced(d, x0 + 80, y0 + 230, "BOOKING" + dots, font("Inter-Bold.otf", 15), (255, 255, 255, 255), 1)


def person_sprite(pts, body, far, facing, prop):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    P = cv.P
    k = AJ.SS
    ink = INK + (255,)
    if prop in ("phone", "selfie", "call", "game", "taxi", "dead"):
        if prop == "call":
            px, py = pts["hl"][0] + 4, pts["hl"][1] + 4
            w, h = 13, 24
        elif prop == "selfie":
            px, py = pts["hl"]
            w, h = 13, 24
        elif prop == "game":
            px = (pts["hl"][0] + pts["hr"][0]) / 2
            py = (pts["hl"][1] + pts["hr"][1]) / 2
            w, h = 24, 13
        else:
            px = (pts["hl"][0] + pts["hr"][0]) / 2
            py = (pts["hl"][1] + pts["hr"][1]) / 2
            w, h = 13, 24
        q0, q1 = P((px - w, py - h)), P((px + w, py + h))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 5 * k, fill=(30, 34, 48, 255), outline=ink, width=3 * k)
        s0, s1 = P((px - w + 4, py - h + 5)), P((px + w - 4, py + h - 5))
        cv.d.rectangle([s0[0], s0[1], s1[0], s1[1]], fill=(4, 4, 6, 255) if prop == "dead" else (140, 200, 255, 255))
    return cv.done()


def battery_widget(d, t, low):
    v = battery(t, low)
    bx, by = W - 270, 60
    col = GREEN if v > 50 else (YELLOW if v > 15 else RED)
    blink = (low or v <= 15) and int(t * 2.5) % 2 == 1
    d.rounded_rectangle([bx, by, bx + 180, by + 76], 12, outline=(236, 238, 244, 255), width=5)
    d.rectangle([bx + 180, by + 24, bx + 194, by + 52], fill=(236, 238, 244, 255))
    fillw = max(6, 168 * v / 100)
    if not blink:
        d.rectangle([bx + 6, by + 6, bx + 6 + fillw, by + 70], fill=col + (255,))
    spaced(d, bx + 90, by + 90, f"{v}%", font(BOLD, 44), (col if not blink else (150, 60, 56)) + (255,), 2)


STREET = None
FRAME0 = None


def panel(t, low):
    im = STREET.copy()
    d = ImageDraw.Draw(im)
    if low:
        if T_CAR0 <= t < T_CAROUT1:
            if t < T_CAR1:
                x = lerp(1200, 560, out_cubic(prog(t, T_CAR0, T_CAR1)))
            elif t < T_CAROUT0:
                x = 560
            else:
                x = lerp(560, -400, in_out(prog(t, T_CAROUT0, T_CAROUT1)))
            draw_taxi(d, x)
    pose, x, y, f, prop, alpha = person(t, low)
    if alpha > 0.01:
        pts = AJ.place(pose, (x, y), f, SC)
        if prop in ("phone", "call", "game", "taxi"):
            OC.phone_glow(im, pts, "phone" if prop != "call" else "call")
        body, far = (LOW, LOW_FAR) if low else (HIGH, HIGH_FAR)
        spr, off = person_sprite(pts, body, far, f, prop)
        if alpha < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
        if low:
            g = PW.glow_of(spr, 0.4, 12)
            if alpha < 0.999:
                g.putalpha(g.split()[3].point(lambda v: int(v * alpha)))
            im.alpha_composite(g, off)
        im.alpha_composite(spr, off)
        d = ImageDraw.Draw(im)
        if prop == "taxi" and not (not low and t >= T_DEAD):
            phone_screen(d, 780 if not low else 820, 330, "app", t)
        if not low and T_DEAD <= t < T_DEAD + 2.2:
            phone_screen(d, 780, 330, "dead", t)
        OC.speech_at(im, t, BUB_LOW if low else BUB_HIGH, pts)
    # the selfie flash
    if T_SELFIE0 + 0.5 <= t < T_SELFIE0 + 0.75:
        a = 1 - prog(t, T_SELFIE0 + 0.5, T_SELFIE0 + 0.75)
        fl = Image.new("RGBA", (W, PH), (255, 255, 255, int(110 * a)))
        im.alpha_composite(fl)
    d = ImageDraw.Draw(im)
    battery_widget(d, t, low)
    if low and t >= 3.0 and t < T_TAXI0 and int(t * 1.2) % 3 == 0:
        spaced(d, W - 180, 196, "STILL 1%", font("Inter-SemiBold.otf", 22), (240, 200, 196, 255), 3)
    return im


def in_out(x):
    return smooth(x)


def frame(t):
    img = Image.new("RGBA", (W, H), (5, 5, 7, 255))
    img.alpha_composite(panel(t, True), (0, TOP_Y0))
    img.alpha_composite(panel(t, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    mm = clock_minutes(t)
    s = f"{mm // 60:02d}:{mm % 60:02d}"
    fc = font(BOLD, 66)
    tw = fc.getlength(s)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, STRIP_Y - 50, W / 2 + tw / 2 + 26, STRIP_Y + 50], 10,
                        fill=(16, 6, 6, 255), outline=(90, 24, 22, 255), width=3)
    g = Image.new("RGBA", (int(tw + 120), 160), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((60, 30), s, font=fc, fill=RED + (200,))
    g = g.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(g, (int(W / 2 - tw / 2 - 60), int(STRIP_Y - 75)))
    d = ImageDraw.Draw(img)
    d.text((W / 2 - tw / 2, STRIP_Y - 41), s, font=fc, fill=RED + (255,))
    fl = font("Inter-SemiBold.otf", 38)
    if t < T_L1:
        spaced(d, W / 2, TOP_Y0 + 14, "1% BATTERY", fl, (240, 242, 248, 255), 8)
    spaced(d, W / 2, BOT_Y0 + 14, "80% BATTERY", fl, (220, 224, 232, 255), 8)
    fm = font(BOLD, 56)
    for t0, s2, y in ((T_L1, LINE1, 40), (T_L2, LINE2, 110)):
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
    global STREET
    STREET = build_street()


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
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    eighth = BEAT / 2
    # a night-time piano pulse in A minor, getting louder towards 2 a.m.; it stops when his screen goes black
    figure = [69, 72, 76, 72, 69, 72, 77, 72]
    chords = [[45, 48, 52], [41, 45, 48], [36, 40, 43], [43, 47, 50]]
    shifts = [0, -4, -9, -2]
    t_end = T_DEAD
    i, tt = 0, 0.1
    while tt < t_end:
        b = int(tt / BAR) % 4
        g = 0.03 + 0.05 * prog(tt, 0, t_end)
        mix_in(mus, OC.piano(midi(figure[i % 8] + shifts[b]), 0.4, 0.5), tt, g, 0.25)
        i += 1
        tt += eighth
    for b in range(int(t_end / BAR) + 1):
        t0 = b * BAR
        if t0 >= t_end:
            break
        ch = chords[b % 4]
        g = 0.03 + 0.04 * prog(t0, 0, t_end)
        for k, m in enumerate(ch):
            mix_in(mus, GS.pad(midi(m), min(BAR, t_end - t0), 0.3, 0.8), t0, g, (k - 1) * 0.4)
        for q in range(4):
            mix_in(mus, OC.piano(midi(ch[0] - 12), 0.5, 0.3), t0 + q * BEAT, g * 1.4)
    # the phone dies: a falling "power off" tone; the taxi: an engine, a door, a horn
    tt2 = np.arange(int(0.6 * SR)) / SR
    mix_in(fx, np.sin(2 * np.pi * np.cumsum(600 * (1 - tt2 / 0.7)) / SR) * np.clip(1 - tt2 / 0.6, 0, 1), T_DEAD, 0.06, 0.3)
    eng = noise(T_CAROUT1 - T_CAR0, 31, lo=60, hi=400)
    te = np.arange(len(eng)) / SR
    eng *= np.minimum(1, te / 0.4) * np.clip((T_CAROUT1 - T_CAR0 - te) / 0.5, 0, 1)
    mix_in(fx, eng, T_CAR0, 0.2, -0.2)
    for j in range(2):
        mix_in(fx, tone(420, 0.18, (1, 0.6, 0.3), a=0.005, d=0.1), T_CAR1 + 0.05 + j * 0.22, 0.05, -0.2)
    mix_in(fx, noise(0.15, 33, lo=100, hi=1500) * env(int(0.15 * SR), 0.002, 0.05), T_GETIN1, 0.15, -0.2)
    # the camera, a call tone, game blips
    mix_in(fx, noise(0.08, 34, lo=2000, hi=8000) * env(int(0.08 * SR), 0.001, 0.02), T_SELFIE0 + 0.5, 0.1)
    for tb in np.arange(T_GAME0, T_GAME1, 0.3):
        mix_in(fx, tone(midi(int(80 + 4 * math.sin(tb * 7))), 0.05, (1, 0.4), a=0.001, d=0.02), tb, 0.02)
    # a cold, quiet chord for the line
    for k, m in enumerate((45, 52, 57, 60)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), 14.6, 0.05, (k - 1.5) * 0.4)
    for j, m in enumerate((76, 72, 69, 72)):
        mix_in(mus, OC.piano(midi(m), 1.3, 0.5), 15.0 + j * 0.5, 0.05, 0.2)
    for b0, b1, s, w in BUB_LOW + BUB_HIGH:
        mix_in(fx, tone(700, 0.07, (1,), a=0.003, d=0.025), b0, 0.025)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "battery.mp4"
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
