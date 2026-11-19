#!/usr/bin/env python3
"""ONE CALLED. ONE SPIRALED. - the "same message, different night" form with our own story, 16.8 s, loops.

Learned from the reference reel: one event lands on both at the same second (a buzz, a banner in the middle strip),
a red digital clock between the two halves that races through the night, the overthinker's thoughts in a three-line
box that keeps rolling and gets more absurd, a reveal that the fear was about nothing, two short opposite lines at the
end, a "FOLLOW FOR MORE" card; a piano figure that keeps pulsing and slowly gets louder, a phone buzz and a few soft
sounds, then a warm resolve.

Our story: 19:42, both on the same couch: "MOM: CALL ME WHEN YOU'RE FREE." The doer calls right away - "HI MOM!" -
"WHAT'S THE WIFI PASSWORD?" - laughs, lies back, falls asleep. The overthinker doesn't call: SOMETHING HAPPENED.
IS DAD OK? DID I FORGET HER BIRTHDAY? ... AM I ADOPTED? He paces, holds his head, stares at the ceiling, hair a mess;
the clock runs to 01:17. He calls at last: "MOM?! WHAT HAPPENED?!" - "...WHAT'S THE WIFI PASSWORD?" - face down.
"ONE CALLED. / ONE SPIRALED."  FOLLOW FOR MORE.

    python3 stick/one_call.py stick/one-called.mp4
    ONLY_FRAMES=0.3,0.9,2.9,5.5,8.2,10.8,12.4,13.6,15.0,16.4 python3 stick/one_call.py /tmp/oc
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
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back, out_cubic,  # noqa
                          prog, rot, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT                          # 2.4 s
DUR = 7 * BAR                           # 16.8 s
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
DOER, DOER_FAR, OT, OT_FAR = AJ.DOER, AJ.DOER_FAR, AJ.OT, AJ.OT_FAR
RED = (255, 64, 56)

# ---------------------------------------------------------------- layout (as the reference: two rooms, a clock between)
PH = 720
TOP_Y0, BOT_Y0 = 150, 1000
STRIP_Y = (TOP_Y0 + PH + BOT_Y0) / 2     # the clock's centre line, 935
FYP = 640                                # floor inside a panel
SEAT = FYP - 140
COUCH_X0, COUCH_X1 = 150, 630
HIP = (360, FYP - 115 * SC)
WIN = (650, 70, 900, 300)
TV = (770, 350, 1010, 500)

# ---------------------------------------------------------------- timeline
T_BUZZ = 0.45
T_BANNER0, T_BANNER1 = 0.55, 2.4
T_CLOCK0, T_CLOCK1 = 2.0, 11.6           # 19:42 -> 01:17
# the doer
T_DPICK, T_DCALL, T_DCONN = 1.0, 1.35, 1.9
T_DHANG = 5.4
T_DLIE0, T_DLIE1 = 5.6, 6.3
T_DSLEEP = 8.0
# the overthinker
THOUGHTS = [(1.9, "SOMETHING HAPPENED."), (2.8, "IS DAD OK?"), (3.7, "DID I FORGET HER BIRTHDAY?"),
            (4.6, "DID SHE SEE MY BANK APP?"), (5.5, "IS SHE SELLING THE HOUSE?"), (6.4, "AM I ADOPTED?"),
            (7.3, "IS THIS ABOUT 2009?"), (8.2, "SHOULD I CALL?"), (9.1, "WHAT IF SHE CRIES?"),
            (10.0, "OK. CALLING."), (10.6, "...IN 5 MINUTES.")]
T_THINK1 = 11.4
T_PACE0, T_PACE1 = 4.4, 6.9
T_HEAD0, T_HEAD1 = 6.9, 8.8
T_LIE0, T_LIE1 = 8.8, 11.4
T_OCALL, T_OCONN = 11.55, 12.7
T_OFLOP = 14.0
T_L1, T_L2 = 14.4, 14.95
CPS = 18.0
LINE1, LINE2 = "ONE CALLED.", "ONE SPIRALED."
T_FOLLOW = 15.75

BUB_DOER = [(1.85, 2.7, "HI MOM!", "me"), (2.75, 4.2, "WHAT'S THE WIFI PASSWORD?", "phone"),
            (4.25, 5.3, "HAHA. \"PIZZA123\".", "me")]
BUB_OT = [(12.0, 12.75, "MOM?! WHAT HAPPENED?!", "me"), (12.8, 14.0, "...WHAT'S THE WIFI PASSWORD?", "phone")]


def clock_minutes(t):
    m = 19 * 60 + 42
    if t >= T_CLOCK0:
        m += 335 * prog(t, T_CLOCK0, T_CLOCK1) ** 1.25
    return int(m) % (24 * 60)


def night(t):
    """0 = dusk, 1 = deep night."""
    return smooth(prog(clock_minutes(t) if clock_minutes(t) > 600 else clock_minutes(t) + 1440, 19 * 60 + 42, 21 * 60))


# ---------------------------------------------------------------- poses (facing right, from the hip)
SIT = dict(AJ.SIT_TYPE, el=(30, -60), hl=(54, -14), er=(26, -56), hr=(50, -10))
SIT_PHONE = dict(AJ.SIT_TYPE, head=(16, -146), neck=(10, -104), el=(28, -66), hl=(48, -98), er=(24, -62), hr=(44, -94))
CALL = dict(AJ.SIT_TYPE, head=(10, -150), neck=(6, -108), el=(36, -110), hl=(18, -150), er=(26, -56), hr=(50, -12))
LAUGH = dict(CALL, head=(-6, -150), neck=(-4, -108), er=(30, -70), hr=(40, -40))
LIE = {"head": (-96, -96), "neck": (-62, -74), "el": (-40, -40), "hl": (-10, -18), "er": (-44, -36), "hr": (-14, -14),
       "kl": (60, -24), "fl": (120, 4), "kr": (56, -18), "fr": (116, 10)}
LIE_PHONE = dict(LIE, el=(-30, -100), hl=(-50, -140), er=(-26, -96), hr=(-46, -136))
HOLD_HEAD = dict(AJ.SIT_TYPE, head=(26, -136), neck=(16, -98), el=(56, -112), hl=(34, -146), er=(52, -108), hr=(30, -142))
STAND = PW.STAND
STAND_PHONE = dict(STAND, el=(26, -66), hl=(44, -100), er=(22, -62), hr=(40, -96))
FLOP = dict(LIE, head=(-104, -70), neck=(-68, -56))


def doer(t):
    """(pose, hip, facing, prop)"""
    if t < T_DPICK:
        return SIT, HIP, 1, "phone_lap"
    if t < T_DCALL:
        k = smooth(prog(t, T_DPICK, T_DCALL))
        return lerp_pose(SIT, SIT_PHONE, k), HIP, 1, "phone"
    if t < T_DHANG:
        k = smooth(prog(t, T_DCALL, T_DCALL + 0.3))
        p = lerp_pose(SIT_PHONE, CALL, k)
        if 4.25 <= t < 5.3:
            p = lerp_pose(CALL, LAUGH, 0.5 + 0.5 * math.sin(t * 14))
        return p, HIP, 1, "call"
    if t < T_DLIE0:
        k = smooth(prog(t, T_DHANG, T_DLIE0))
        return lerp_pose(CALL, SIT, k), HIP, 1, "phone_lap"
    k = smooth(prog(t, T_DLIE0, T_DLIE1))
    hip = (lerp(HIP[0], 420, k), lerp(HIP[1], SEAT - 26, k))
    return lerp_pose(SIT, LIE, k), hip, 1, ("sleep" if t >= T_DSLEEP else "relax")


def overthinker(t):
    if t < 1.2:
        k = smooth(prog(t, 0.6, 1.2))
        return lerp_pose(SIT, SIT_PHONE, k), HIP, 1, "phone" if k > 0.3 else "phone_lap"
    if t < T_PACE0:
        return SIT_PHONE, HIP, 1, "phone"
    if t < T_PACE1:
        # up and pacing the room, phone in hand
        u = prog(t, T_PACE0, T_PACE1)
        if u < 0.12:
            k = smooth(u / 0.12)
            return lerp_pose(SIT_PHONE, STAND_PHONE, k), (HIP[0], lerp(HIP[1], FYP - 113 * SC, k)), 1, "phone"
        if u > 0.88:
            k = smooth((u - 0.88) / 0.12)
            return lerp_pose(STAND_PHONE, SIT_PHONE, k), (HIP[0], lerp(FYP - 113 * SC, HIP[1], k)), 1, "phone"
        v = (u - 0.12) / 0.76
        ph = v * 2 * math.pi
        x = HIP[0] + 330 * (0.5 - 0.5 * math.cos(ph))
        f = 1 if math.sin(ph) >= 0 else -1
        return AJ.walk(t * 7, STAND_PHONE), (x, FYP - 113 * SC), f, "phone"
    if t < T_HEAD1:
        k = smooth(prog(t, T_HEAD0, T_HEAD0 + 0.3))
        rock = 0.5 + 0.5 * math.sin(t * 6)
        p = lerp_pose(SIT_PHONE, HOLD_HEAD, k)
        p = dict(p, head=(p["head"][0] + 6 * rock, p["head"][1]))
        return p, HIP, 1, None
    if t < T_LIE1:
        k = smooth(prog(t, T_LIE0, T_LIE0 + 0.5))
        hip = (lerp(HIP[0], 420, k), lerp(HIP[1], SEAT - 26, k))
        return lerp_pose(HOLD_HEAD, LIE_PHONE, k), hip, 1, "phone_up"
    if t < T_OFLOP:
        k = smooth(prog(t, T_LIE1, T_OCALL + 0.3))
        hip = (lerp(420, HIP[0], k), lerp(SEAT - 26, HIP[1], k))
        return lerp_pose(LIE_PHONE, CALL, k), hip, 1, "call"
    k = smooth(prog(t, T_OFLOP, T_OFLOP + 0.35))
    hip = (lerp(HIP[0], 420, k), lerp(HIP[1], SEAT - 20, k))
    return lerp_pose(CALL, FLOP, k), hip, 1, "phone_drop"


# ---------------------------------------------------------------- the room
def build_room():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + 7
    lamp = np.exp(-(((xx - 90) / 300) ** 2 + ((yy - (FYP - 250)) / 260) ** 2))
    img += lamp[..., None] * np.array([60, 44, 26], np.float32)
    floor = yy > FYP
    img = np.where(floor[..., None], img * 0.8 + 8, img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(46, 44, 44, 255), width=2)
    # side table + lamp
    d.rectangle([40, FYP - 150, 130, FYP - 136], fill=(64, 58, 54, 255), outline=ink, width=3)
    for x in (48, 116):
        d.rectangle([x, FYP - 136, x + 8, FYP], fill=(54, 50, 48, 255))
    d.line([(85, FYP - 150), (85, FYP - 236)], fill=(80, 80, 84, 255), width=4)
    d.polygon([(52, FYP - 236), (118, FYP - 236), (104, FYP - 286), (66, FYP - 286)], fill=(236, 206, 150, 255),
              outline=ink)
    # TV on a stand
    x0, y0, x1, y1 = TV
    d.rectangle([(x0 + x1) / 2 - 70, y1 + 50, (x0 + x1) / 2 + 70, FYP], fill=(46, 44, 46, 255), outline=ink, width=3)
    d.rectangle([(x0 + x1) / 2 - 6, y1, (x0 + x1) / 2 + 6, y1 + 50], fill=(46, 46, 50, 255))
    d.rounded_rectangle([x0 - 8, y0 - 8, x1 + 8, y1 + 8], 6, fill=(30, 30, 34, 255), outline=ink, width=3)
    # the couch: back, seat, arms
    d.rounded_rectangle([COUCH_X0 + 10, FYP - 290, COUCH_X1 - 10, SEAT + 10], 24, fill=(74, 78, 96, 255), outline=ink,
                        width=4)
    d.rounded_rectangle([COUCH_X0, SEAT, COUCH_X1, FYP - 40], 16, fill=(84, 88, 108, 255), outline=ink, width=4)
    for ax in (COUCH_X0 - 26, COUCH_X1 - 26):
        d.rounded_rectangle([ax, FYP - 210, ax + 52, FYP - 40], 18, fill=(70, 74, 92, 255), outline=ink, width=4)
    for lx in (COUCH_X0 + 10, COUCH_X1 - 22):
        d.rectangle([lx, FYP - 40, lx + 12, FYP], fill=(40, 38, 40, 255))
    d.line([(COUCH_X0 + 250, SEAT + 4), (COUCH_X0 + 250, FYP - 44)], fill=(60, 64, 80, 255), width=3)
    return im


def draw_window(im, d, t):
    x0, y0, x1, y1 = WIN
    n = night(t)
    sky_top = PW.lerp_c((70, 60, 110), (10, 14, 34), n)
    sky_bot = PW.lerp_c((240, 140, 90), (24, 30, 60), n)
    for i in range(y1 - y0):
        c = PW.lerp_c(sky_top, sky_bot, i / (y1 - y0))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (255,))
    rng = np.random.default_rng(1)
    # the city: windows go on at night
    for i in range(7):
        bx = x0 + 6 + i * 36
        bh = 40 + (i * 37) % 70
        d.rectangle([bx, y1 - bh, bx + 30, y1], fill=(14, 16, 28, 255))
        for j in range(int(bh / 16)):
            if rng.uniform() < 0.3 + 0.5 * n:
                d.rectangle([bx + 8, y1 - bh + 6 + j * 16, bx + 14, y1 - bh + 12 + j * 16], fill=(255, 210, 120, 255))
    if n > 0.3:
        a = int(255 * smooth((n - 0.3) / 0.5))
        d.ellipse([x1 - 70, y0 + 24, x1 - 40, y0 + 54], fill=(240, 238, 220, a))
        d.ellipse([x1 - 62, y0 + 20, x1 - 34, y0 + 48], fill=sky_top + (a,))
        for k in range(8):
            sx, sy = x0 + rng.uniform(10, x1 - x0 - 10), y0 + rng.uniform(8, 80)
            d.ellipse([sx - 1.5, sy - 1.5, sx + 1.5, sy + 1.5], fill=(220, 220, 240, a))
    ink = INK + (255,)
    d.rectangle([x0, y0, x1, y1], outline=ink, width=8)
    d.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=ink, width=6)
    d.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=ink, width=6)
    d.rectangle([x0 - 14, y1, x1 + 14, y1 + 12], fill=(60, 56, 54, 255), outline=ink, width=3)


def draw_tv(im, d, t, on):
    x0, y0, x1, y1 = TV
    if not on:
        d.rectangle([x0, y0, x1, y1], fill=(12, 13, 18, 255))
        return
    c = PW.lerp_c((40, 70, 130), (70, 110, 170), 0.5 + 0.5 * math.sin(t * 5))
    d.rectangle([x0, y0, x1, y1], fill=c + (255,))
    for i in range(4):
        y = y0 + 20 + i * 30
        d.line([(x0 + 20, y), (x0 + 60 + 120 * abs(math.sin(i * 1.7 + int(t * 2))), y)], fill=(150, 190, 240, 255), width=6)
    g = Image.new("RGBA", (500, 400), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([60, 60, 440, 340], fill=c + (60,))
    g = g.filter(ImageFilter.GaussianBlur(50))
    im.alpha_composite(g, (int((x0 + x1) / 2 - 250 - 80), int((y0 + y1) / 2 - 200)))


def person_sprite(pts, body, far, facing, prop, t, mess=0.0):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    P = cv.P
    k = AJ.SS
    ink = INK + (255,)
    hx, hy = pts["head"]
    if mess > 0.05:
        # stress scribbles over the head, more and more
        rng = np.random.default_rng(7)
        for i in range(int(2 + 5 * mess)):
            a0 = rng.uniform(-2.6, -0.6)
            r = 46 * SC
            sx, sy = hx + r * math.cos(a0), hy + r * math.sin(a0)
            pts2 = [P((sx, sy))]
            for j in range(4):
                sx += rng.uniform(-10, 10)
                sy += rng.uniform(-14, -2)
                pts2.append(P((sx, sy)))
            cv.d.line(pts2, fill=ink, width=5 * k, joint="curve")
    if prop in ("phone", "call", "phone_up"):
        if prop == "call":
            ph = pts["hl"]
            px, py = ph[0] + 4, ph[1] + 4
        else:
            px = (pts["hl"][0] + pts["hr"][0]) / 2
            py = (pts["hl"][1] + pts["hr"][1]) / 2
        q0, q1 = P((px - 13, py - 24)), P((px + 13, py + 24))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 5 * k, fill=(30, 34, 48, 255), outline=ink, width=3 * k)
        s0, s1 = P((px - 9, py - 19)), P((px + 9, py + 19))
        cv.d.rectangle([s0[0], s0[1], s1[0], s1[1]], fill=(140, 200, 255, 255))
        for hn in ("hl", "hr") if prop != "call" else ("hl",):
            AJ.disc(cv, pts[hn], 11 * SC + 6 * SC, ink)
            AJ.disc(cv, pts[hn], 11 * SC, body + (255,))
    spr, off = cv.done()
    return spr, off


def phone_glow(im, pts, prop):
    if prop not in ("phone", "call", "phone_up"):
        return
    if prop == "call":
        px, py = pts["hl"]
    else:
        px = (pts["hl"][0] + pts["hr"][0]) / 2
        py = (pts["hl"][1] + pts["hr"][1]) / 2
    g = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([80, 80, 220, 220], fill=(120, 180, 255, 120))
    g = g.filter(ImageFilter.GaussianBlur(30))
    im.alpha_composite(g, (int(px - 150), int(py - 150)))


def thought_box(im, t, head):
    """The overthinker's three rolling lines (the newest at the bottom, bold)."""
    shown = [(t0, s) for t0, s in THOUGHTS if t0 <= t]
    if not shown or t >= T_THINK1:
        return
    lines = shown[-3:]
    f_old = font(MONO, 33)
    f_new = font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 36)
    wmax = max(f_new.getlength(s) + 2 * len(s) for _, s in lines)
    bw, bh = int(wmax + 50), 44 * len(lines) + 28
    k = 2
    box = Image.new("RGBA", (bw * k, bh * k), (0, 0, 0, 0))
    bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([2 * k, 2 * k, (bw - 2) * k, (bh - 2) * k], 14 * k, fill=(10, 12, 18, 240),
                         outline=(236, 238, 244, 255), width=3 * k)
    box = box.reduce(k)
    bd = ImageDraw.Draw(box)
    for i, (t0, s) in enumerate(lines):
        newest = i == len(lines) - 1
        pop = out_back(prog(t, t0, t0 + 0.18)) if newest else 1.0
        a = 255 if newest else (150 if i == len(lines) - 2 else 100)
        spaced(bd, bw / 2, 14 + i * 44 + (1 - pop) * 10, s, f_new if newest else f_old, (240, 242, 248, a), 2)
    hx, hy = head
    x = clamp(hx - bw / 2 + 60, 20, W - 20 - bw)
    y = max(56, hy - 120 - bh)
    al = 1 - smooth(prog(t, T_THINK1 - 0.2, T_THINK1))
    if al < 0.999:
        box.putalpha(box.split()[3].point(lambda v: int(v * al)))
    im.alpha_composite(box, (int(x), int(y)))
    d = ImageDraw.Draw(im)
    for r, ox, oy in ((5, 10, 60), (8, 22, 86)):
        d.ellipse([hx + ox - r, hy - oy - r, hx + ox + r, hy - oy + r], outline=(236, 238, 244, int(255 * al)), width=3)


_bubs = {}


def speech(s, phone=False):
    key = (s, phone)
    if key in _bubs:
        return _bubs[key]
    f = font(MONO, 29)
    lw = f.getlength(s) + 2 * (len(s) - 1)
    pad = 54 if phone else 36
    pw, ph = int(lw + pad + 10), 56
    k = 2
    im = Image.new("RGBA", (pw * k, (ph + 20) * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fill = (214, 234, 255, 255) if phone else (242, 240, 234, 255)
    d.rounded_rectangle([3 * k, 3 * k, (pw - 3) * k, (ph - 3) * k], 12 * k, fill=fill, outline=INK + (255,), width=4 * k)
    tx = pw * 0.35
    d.polygon([((tx - 10) * k, (ph - 6) * k), ((tx + 10) * k, (ph - 6) * k), ((tx - 4) * k, (ph + 16) * k)], fill=INK + (255,))
    d.polygon([((tx - 6) * k, (ph - 8) * k), ((tx + 6) * k, (ph - 8) * k), ((tx - 3) * k, (ph + 7) * k)], fill=fill)
    im = im.reduce(k)
    dd = ImageDraw.Draw(im)
    x0 = 18
    if phone:
        dd.rounded_rectangle([14, 14, 34, 42], 4, fill=(30, 34, 48, 255))
        dd.rectangle([17, 17, 31, 38], fill=(120, 180, 255, 255))
        x0 = 44
    xx = x0
    for c in s:
        dd.text((xx, 12), c, font=f, fill=INK + (255,))
        xx += f.getlength(c) + 2
    _bubs[key] = im
    return im


def speech_at(im, t, lst, pts):
    for b0, b1, s, who in lst:
        if not (b0 <= t < b1):
            continue
        spr = speech(s, who == "phone")
        sc = out_back(prog(t, b0, b0 + 0.16))
        al = 1 - smooth(prog(t, b1 - 0.1, b1))
        if sc < 0.05:
            continue
        spr = spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.LANCZOS)
        if al < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * al)))
        hx, hy = pts["head"]
        x = clamp(hx - spr.width * 0.3, 16, W - 16 - spr.width)
        y = max(52, hy - 70 - spr.height)
        im.alpha_composite(spr, (int(x), int(y)))


ROOM = None
FRAME0 = None


def panel(t, top):
    im = ROOM.copy()
    d = ImageDraw.Draw(im)
    draw_window(im, d, t)
    if top:
        pose, hip, f, prop = overthinker(t)
        tv_on = t < T_PACE0
    else:
        pose, hip, f, prop = doer(t)
        tv_on = t < T_DSLEEP
    draw_tv(im, d, t, tv_on)
    d = ImageDraw.Draw(im)
    pts = AJ.place(pose, hip, f, SC)
    body, far = (OT, OT_FAR) if top else (DOER, DOER_FAR)
    mess = smooth(prog(t, 3.0, 11.0)) if top else 0.0
    phone_glow(im, pts, prop)
    spr, off = person_sprite(pts, body, far, f, prop, t, mess)
    if not top:
        im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    # the phone buzzing on the lap at the start
    if prop == "phone_lap" or (prop is None and not top):
        px, py = pts["hl"][0] + 6, pts["hl"][1] - 6
        jig = 3 * math.sin(t * 90) if T_BUZZ <= t < T_BUZZ + 0.5 else 0
        d.rounded_rectangle([px - 22 + jig, py - 8, px + 22 + jig, py + 6], 4, fill=(30, 34, 48, 255), outline=INK + (255,),
                            width=3)
        if T_BUZZ <= t < T_BUZZ + 0.5:
            for s in (-1, 1):
                d.arc([px - 40 + s * 8, py - 30, px + 40 + s * 8, py + 24], 200 if s < 0 else 300, 240 if s < 0 else 340,
                      fill=(240, 240, 244, 255), width=3)
    if prop == "phone_drop":
        px, py = HIP[0] + 150, SEAT - 6
        d.rounded_rectangle([px - 22, py - 8, px + 22, py + 6], 4, fill=(30, 34, 48, 255), outline=INK + (255,), width=3)
    if not top and prop == "sleep":
        for i in range(2):
            ph = (t * 0.7 + i * 0.5) % 1.0
            hx, hy = pts["head"]
            d.text((hx + 20 + 26 * ph + i * 12, hy - 50 - 50 * ph), "z", font=font("Inter-Bold.otf", 26 + 8 * i),
                   fill=(220, 226, 240, int(255 * math.sin(math.pi * ph))))
    if top:
        thought_box(im, t, pts["head"])
        speech_at(im, t, BUB_OT, pts)
        if t >= T_OFLOP + 0.3:
            d.text((pts["head"][0] - 30, pts["head"][1] - 80), "...", font=font("Inter-Bold.otf", 40),
                   fill=(220, 222, 230, 255))
    else:
        speech_at(im, t, BUB_DOER, pts)
    return im


def banner(img, t):
    if not (T_BANNER0 <= t < T_BANNER1):
        return
    u_in = out_cubic(prog(t, T_BANNER0, T_BANNER0 + 0.25))
    a = 1 - smooth(prog(t, T_BANNER1 - 0.25, T_BANNER1))
    bw, bh = 640, 104
    x0 = W / 2 - bw / 2
    y0 = STRIP_Y - bh / 2 - 40 * (1 - u_in)
    b = Image.new("RGBA", (bw * 2, bh * 2), (0, 0, 0, 0))
    bd = ImageDraw.Draw(b)
    bd.rounded_rectangle([0, 0, bw * 2 - 1, bh * 2 - 1], 30, fill=(246, 246, 248, 255))
    b = b.reduce(2)
    bd = ImageDraw.Draw(b)
    bd.rounded_rectangle([18, 16, 50, 48], 8, fill=(52, 199, 89, 255))
    bd.rounded_rectangle([25, 24, 43, 38], 4, fill=(255, 255, 255, 255))
    bd.text((64, 16), "MOM", font=font("Inter-Bold.otf", 26), fill=(20, 20, 24, 255))
    bd.text((bw - 64, 20), "now", font=font("Inter-Regular.otf", 20), fill=(130, 130, 140, 255))
    bd.text((22, 58), "CALL ME WHEN YOU'RE FREE.", font=font(MONO, 26), fill=(30, 30, 36, 255))
    if a < 0.999:
        b.putalpha(b.split()[3].point(lambda v: int(v * a)))
    img.alpha_composite(b, (int(x0), int(y0)))


def frame(t):
    img = Image.new("RGBA", (W, H), (5, 5, 7, 255))
    img.alpha_composite(panel(t, True), (0, TOP_Y0))
    img.alpha_composite(panel(t, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    # the strip and the red clock
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    m = clock_minutes(t)
    s = f"{m // 60:02d}:{m % 60:02d}"
    fc = font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 66)
    tw = fc.getlength(s)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, STRIP_Y - 50, W / 2 + tw / 2 + 26, STRIP_Y + 50], 10,
                        fill=(16, 6, 6, 255), outline=(90, 24, 22, 255), width=3)
    g = Image.new("RGBA", (int(tw + 120), 160), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((60, 30), s, font=fc, fill=RED + (200,))
    g = g.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(g, (int(W / 2 - tw / 2 - 60), int(STRIP_Y - 75)))
    d = ImageDraw.Draw(img)
    d.text((W / 2 - tw / 2, STRIP_Y - 41), s, font=fc, fill=RED + (255,))
    banner(img, t)
    d = ImageDraw.Draw(img)
    # labels, then the line in their place
    fl = font("Inter-SemiBold.otf", 38)
    if t < T_L1:
        spaced(d, W / 2, TOP_Y0 + 14, "OVERTHINKER", fl, (220, 224, 232, 255), 10)
    spaced(d, W / 2, BOT_Y0 + 14, "DOER", fl, (240, 242, 248, 255), 10)
    fm = font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 60)
    for t0, s2, y in ((T_L1, LINE1, 40), (T_L2, LINE2, 112)):
        if t < t0:
            continue
        k = int(clamp((t - t0) * CPS, 0, len(s2)))
        full = sum(fm.getlength(c) for c in s2) + 4 * (len(s2) - 1)
        xx = W / 2 - full / 2
        for c in s2[:k]:
            d.text((xx, y), c, font=fm, fill=(250, 250, 252, 255))
            xx += fm.getlength(c) + 4
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    # the end card: dim everything, FOLLOW FOR MORE
    if t >= T_FOLLOW:
        k = smooth(prog(t, T_FOLLOW, T_FOLLOW + 0.3))
        arr *= 1 - 0.75 * k
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        ff = font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 76)
        spaced(cd, W / 2, H / 2 - 90, "FOLLOW", ff, (250, 250, 252, int(255 * k)), 6)
        spaced(cd, W / 2, H / 2 + 6, "FOR MORE", ff, (250, 250, 252, int(255 * k)), 6)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        base.alpha_composite(card)
        return np.asarray(base.convert("RGB"))
    return np.clip(arr, 0, 255).astype(np.uint8)


def init_worker():
    global ROOM
    ROOM = build_room()


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


# ---------------------------------------------------------------- sound: a pulsing piano that keeps rising, then a warm resolve
def piano(f, dur=1.4, bright=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) + 0.5 * bright * np.sin(4 * np.pi * f * t) * np.exp(-t * 4)
         + 0.2 * bright * np.sin(6 * np.pi * f * t) * np.exp(-t * 7))
    return x * np.minimum(1, t / 0.004) * np.exp(-t * 2.6)


def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    eighth = BEAT / 2
    # D minor: the pulse alternates A4 and Bb4 (the semitone keeps it uneasy), a low D under it,
    # one chord a bar (Dm, Bb, Gm, A) - all of it getting louder as the night goes on
    chords = [[50, 53, 57], [46, 50, 53], [43, 46, 50], [45, 49, 52]]
    t_end = T_OCONN + 0.1
    i = 0
    tt = 0.5
    while tt < t_end:
        g = 0.035 + 0.075 * prog(tt, 0.5, 11.5) ** 1.3
        note = [69, 70][i % 2] if i % 8 < 6 else [72, 70][i % 2]
        mix_in(mus, piano(midi(note), 0.6, 0.5), tt, g, 0.25)
        if prog(tt, 5.0, 6.0) > 0:
            mix_in(mus, piano(midi(note - 12), 0.6, 0.4), tt, g * 0.6 * prog(tt, 5.0, 6.0), -0.25)
        i += 1
        tt += eighth
    for b in range(int(t_end / BAR) + 1):
        t0 = b * BAR
        if t0 >= t_end:
            break
        ch = chords[b % 4]
        g = 0.03 + 0.05 * prog(t0, 0, 11)
        dur = min(BAR, t_end - t0) + 0.6
        for k, m in enumerate(ch):
            mix_in(mus, GS.pad(midi(m), dur - 0.6, 0.4, 0.8), t0, g, (k - 1) * 0.4)
        mix_in(mus, piano(midi(ch[0] - 12), 2.4, 0.3), t0, g * 2.2)
    # while she talks: only a low, quiet D under the line
    mix_in(mus, GS.pad(midi(38), 1.6, 0.2, 0.6), T_OCONN, 0.06)
    mix_in(mus, GS.pad(midi(50), 1.6, 0.2, 0.6), T_OCONN, 0.025)
    # after the second call connects: the line, then a warm F major, soft
    for k, m in enumerate((53, 57, 60, 65)):
        mix_in(mus, GS.pad(midi(m), 2.6, 0.6, 1.6), 14.3, 0.05, (k - 1.5) * 0.4)
    for j, m in enumerate((72, 69, 65, 69, 72)):
        mix_in(mus, piano(midi(m), 1.4, 0.5), 14.4 + j * 0.45, 0.06, 0.2)
    # the phone buzz on both laps and the doer's ringing
    tb = np.arange(int(0.42 * SR)) / SR
    buzz = np.sign(np.sin(2 * np.pi * 150 * tb)) * 0.6 * (np.sin(2 * np.pi * 9 * tb) > -0.2)
    buzz = PW.filt(buzz, hi=900) * np.minimum(1, tb / 0.02) * np.clip((0.42 - tb) / 0.05, 0, 1)
    mix_in(fx, buzz, T_BUZZ, 0.1)
    mix_in(fx, piano(midi(88), 0.4, 0.3), T_BANNER0 + 0.05, 0.08)
    mix_in(fx, piano(midi(84), 0.4, 0.3), T_BANNER0 + 0.15, 0.08)

    def ring(t0, times):
        for r in range(times):
            tr = np.arange(int(0.45 * SR)) / SR
            s = (np.sin(2 * np.pi * 440 * tr) + np.sin(2 * np.pi * 480 * tr)) * np.minimum(1, tr / 0.02) * np.clip((0.45 - tr) / 0.05, 0, 1)
            mix_in(fx, s, t0 + r * 0.7, 0.04, 0.0)

    ring(T_DCALL + 0.05, 1)
    ring(T_OCALL + 0.05, 2)
    mix_in(fx, tone(1200, 0.06, (1,), a=0.002, d=0.02), T_DCONN, 0.06, -0.3)
    mix_in(fx, tone(1200, 0.06, (1,), a=0.002, d=0.02), T_OCONN - 0.05, 0.06, 0.3)
    # footsteps while pacing; a cushion when he flops
    for ts in np.arange(T_PACE0 + 0.4, T_PACE1 - 0.3, BEAT / 1.5):
        mix_in(fx, noise(0.05, int(ts * 100), lo=300, hi=2000) * env(int(0.05 * SR), 0.002, 0.015), ts, 0.05, 0.3)
    mix_in(fx, noise(0.3, 9, lo=60, hi=600) * env(int(0.3 * SR), 0.003, 0.09), T_OFLOP + 0.3, 0.25, 0.3)
    # the doer laughs: three soft notes; falls asleep: a low hum
    for j, m in enumerate((76, 79, 76)):
        mix_in(fx, piano(midi(m), 0.3, 0.3), 4.3 + j * 0.16, 0.03, -0.3)
    for b0, b1, s, w in BUB_DOER + BUB_OT:
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
    out = sys.argv[1] if len(sys.argv) > 1 else "one-called.mp4"
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
