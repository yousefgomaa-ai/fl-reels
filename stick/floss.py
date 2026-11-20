#!/usr/bin/env python3
"""IDEAS.md #8 - "DO YOU FLOSS?" "YES." Split screen, 18 s, loops on itself.

DENTIST IN 30 DAYS, the same bathroom, the same box of floss. Above, he flosses every night: FLOSSED 30/30.
Below: "TOMORROW." "TOO TIRED." "BRUSHING IS ENOUGH." - 0/30 - then, the night before, he flosses like mad: "OW."
"LAST NIGHT COUNTS." TODAY, the dentist: "DO YOU FLOSS?" Both: "YES." Close-up: pink gums above, red ones below.
"GREAT GUMS." / "...SINCE LAST NIGHT?"  "HE SAID YES. / HIS GUMS SAID NO."  FOLLOW FOR MORE.

    VARIANT=A python3 stick/floss.py stick/floss-A.mp4      # current style
    VARIANT=B python3 stick/floss.py stick/floss-B.mp4      # stronger first second
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
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          prog, smooth, spaced, tone, write_wav)

VARIANT = os.environ.get("VARIANT", "A").upper()
STRONG = VARIANT == "B"

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
GOOD_C, GOOD_FAR = AJ.DOER, AJ.DOER_FAR
LIE_C, LIE_FAR = AJ.OT, AJ.OT_FAR
DOC_C, DOC_FAR = (150, 205, 225), (110, 160, 180)
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141

# ---------------------------------------------------------------- timeline
T_N0, T_N1 = 0.6, 8.6                      # nights: 30 days left -> 1
T_CRAM0, T_CRAM1 = 7.4, 8.9
T_CUT = 9.4                                # bathroom -> dentist
T_ASK, T_YES, T_LOOK, T_VERDICT = 10.0, 10.9, 11.8, 12.7
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "HE SAID YES.", "HIS GUMS SAID NO."
T_FOLLOW = 16.95

B0 = -0.3 if STRONG else 0.3
BUB_GOOD = [(B0, 1.4, "FLOSS. EVERY NIGHT.", "me"), (T_YES, T_YES + 1.0, "YES.", "me")]
BUB_LIE = [(B0, 1.4, "FLOSS? TOMORROW.", "me"), (2.4, 3.3, "TOO TIRED.", "me"), (4.3, 5.3, "BRUSHING IS ENOUGH.", "me"),
           (7.5, 8.1, "OW.", "me"), (8.1, 9.0, "LAST NIGHT COUNTS.", "me"), (T_YES, T_YES + 1.0, "YES.", "me"),
           (13.9, 14.9, "...MAYBE.", "me")]
DOC_GOOD = [(T_ASK, T_ASK + 0.9, "DO YOU FLOSS?", "me"), (T_VERDICT, T_VERDICT + 1.6, "GREAT GUMS.", "me")]
DOC_LIE = [(T_ASK, T_ASK + 0.9, "DO YOU FLOSS?", "me"), (T_VERDICT, T_VERDICT + 1.2, "SINCE LAST NIGHT?", "me")]


def days_left(t):
    return max(1, int(round(30 - 29 * prog(t, T_N0, T_N1))))


def flossed(t, good):
    if good:
        return min(30, 30 - days_left(t) + 1)
    return 1 if t >= T_CRAM0 + 0.4 else 0


# ---------------------------------------------------------------- poses
STAND = PW.STAND
BRUSH = dict(STAND, el=(30, -84), hl=(10, -60), er=(34, -86), hr=(40, -134))
FLOSS = dict(STAND, el=(28, -96), hl=(22, -138), er=(36, -90), hr=(46, -132))
LOOK = dict(BRUSH, head=(10, -146))
PATIENT = OC.LIE
DOC = dict(STAND, head=(10, -150), el=(44, -118), hl=(92, -148), er=(36, -78), hr=(64, -84))
DOC_LOOK = dict(DOC, head=(26, -142), neck=(14, -104))

SINK_X = 560
PERSON = (420, STAND_Y)


def bath_person(t, good):
    """pose, prop"""
    if good:
        if t < T_N0:
            return BRUSH, "brush"
        ph = (t - T_N0) % 2.4
        if ph < 0.8:
            p = dict(BRUSH, hr=(40 + 6 * math.sin(t * 30), -134))
            return p, "brush"
        p = dict(FLOSS, hl=(22, -138 + 6 * math.sin(t * 16)), hr=(46, -132 + 6 * math.sin(t * 16)))
        return p, "floss"
    if T_CRAM0 <= t < T_CRAM1:
        p = dict(FLOSS, hl=(22, -138 + 12 * math.sin(t * 40)), hr=(46, -132 + 12 * math.sin(t * 40)))
        return p, "floss"
    for b0, b1, s, w in BUB_LIE[:3]:
        if b0 <= t < b1:
            return LOOK, "brush"
    return dict(BRUSH, hr=(40 + 6 * math.sin(t * 30), -134)), "brush"


# ---------------------------------------------------------------- rooms
def wall(top_rgb):
    if STRONG:
        return tuple(min(255, c + 22) for c in top_rgb)
    return top_rgb


def build_bath():
    base = np.array(wall((9, 10, 12)), np.float32)
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + base
    # tiles
    tile = ((xx // 60 + yy // 60) % 2 == 0) & (yy > FYP - 330) & (yy < FYP)
    img = np.where(tile[..., None], img + 6, img)
    img = np.where((yy > FYP)[..., None], img * 0.75 + 6, img)
    if STRONG:
        r = np.sqrt((xx - 540) ** 2 + (yy - 30) ** 2)
        img += (np.exp(-(r / 520) ** 2) * 34)[..., None] * np.array([1.0, 0.95, 0.85])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(56, 54, 54, 255), width=2)
    # mirror
    d.rounded_rectangle([SINK_X - 40, 120, SINK_X + 160, 330], 14, fill=(150, 176, 196, 255), outline=ink, width=6)
    d.line([(SINK_X + 10, 150), (SINK_X + 60, 210)], fill=(220, 236, 246, 255), width=8)
    # sink
    d.rounded_rectangle([SINK_X - 20, FYP - 250, SINK_X + 150, FYP - 214], 10, fill=(236, 238, 244, 255), outline=ink,
                        width=4)
    d.rectangle([SINK_X + 40, FYP - 214, SINK_X + 90, FYP], fill=(220, 222, 230, 255), outline=ink, width=4)
    d.rectangle([SINK_X + 100, FYP - 280, SINK_X + 112, FYP - 250], fill=(180, 184, 194, 255), outline=ink, width=3)
    d.line([(SINK_X + 106, FYP - 280), (SINK_X + 80, FYP - 280)], fill=ink, width=6)
    # floss box on the sink
    d.rounded_rectangle([SINK_X + 4, FYP - 284, SINK_X + 44, FYP - 250], 6, fill=(250, 250, 252, 255), outline=ink,
                        width=3)
    d.rectangle([SINK_X + 4, FYP - 284, SINK_X + 44, FYP - 274], fill=(90, 170, 220, 255))
    # a small window with the night
    d.rectangle([150, 120, 300, 260], fill=(14, 18, 40, 255), outline=ink, width=6)
    d.ellipse([250, 140, 276, 166], fill=(240, 238, 220, 255))
    return im


CHAIR_HIP = (560, FYP - 196)


def build_clinic():
    base = np.array(wall((12, 14, 16)), np.float32)
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + base + np.array([0, 4, 6])
    img = np.where((yy > FYP)[..., None], img * 0.75 + 6, img)
    if STRONG:
        r = np.sqrt((xx - 540) ** 2 + (yy - 30) ** 2)
        img += (np.exp(-(r / 520) ** 2) * 34)[..., None] * np.array([0.9, 1.0, 1.0])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(56, 54, 54, 255), width=2)
    hx, hy = CHAIR_HIP
    # dentist chair
    d.polygon([(hx - 40, hy + 14), (hx + 200, hy - 6), (hx + 210, hy + 30), (hx - 30, hy + 50)],
              fill=(90, 170, 190, 255), outline=ink)
    d.polygon([(hx - 40, hy + 14), (hx - 200, hy - 110), (hx - 180, hy - 140), (hx - 20, hy - 20)],
              fill=(90, 170, 190, 255), outline=ink)
    d.rectangle([hx + 40, hy + 40, hx + 80, FYP - 20], fill=(180, 184, 194, 255), outline=ink, width=4)
    d.rounded_rectangle([hx - 20, FYP - 24, hx + 140, FYP], 8, fill=(180, 184, 194, 255), outline=ink, width=4)
    # lamp
    d.line([(hx - 120, 70), (hx - 120, 90), (hx - 170, 130)], fill=(180, 184, 194, 255), width=8)
    d.ellipse([hx - 210, 110, hx - 140, 160], fill=(255, 240, 190, 255), outline=ink, width=4)
    return im


def draw_brush(d, pts, prop, t):
    ink = INK + (255,)
    if prop == "brush":
        hx, hy = pts["hr"]
        d.line([(hx - 4, hy + 10), (hx + 10, hy - 22)], fill=(90, 170, 220, 255), width=8)
        d.ellipse([hx - 8, hy + 6, hx + 2, hy + 16], fill=ink)
    elif prop == "floss":
        a, b = pts["hl"], pts["hr"]
        d.line([a, (pts["head"][0] + 26, pts["head"][1] + 18), b], fill=(250, 250, 252, 255), width=3)


def mouth_inset(im, t, healthy):
    k = smooth(prog(t, T_LOOK, T_LOOK + 0.35))
    if k <= 0:
        return
    R = int(150 * out_back(k))
    if R < 8:
        return
    cx, cy = 860, 260
    sz = 2 * 150 + 20
    spr = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    c = sz // 2
    ink = INK + (255,)
    d.ellipse([c - 150, c - 150, c + 150, c + 150], fill=(60, 20, 26, 255))
    gum = (240, 140, 150) if healthy else (205, 40, 50)
    # upper and lower gums
    d.chord([c - 130, c - 120, c + 130, c + 20], 180, 360, fill=gum + (255,))
    d.chord([c - 130, c - 20, c + 130, c + 120], 0, 180, fill=gum + (255,))
    for j in range(6):
        x = c - 105 + j * 36
        d.rounded_rectangle([x, c - 62, x + 30, c - 12], 8, fill=(250, 250, 246, 255), outline=(200, 200, 196, 255),
                            width=2)
        d.rounded_rectangle([x + 2, c + 12, x + 32, c + 58], 8, fill=(250, 250, 246, 255), outline=(200, 200, 196, 255),
                            width=2)
    if healthy:
        for sx, sy in ((c - 70, c - 80), (c + 60, c - 70), (c + 10, c + 70)):
            s = 10 + 4 * math.sin(t * 8 + sx)
            d.line([(sx - s, sy), (sx + s, sy)], fill=(255, 255, 255, 255), width=3)
            d.line([(sx, sy - s), (sx, sy + s)], fill=(255, 255, 255, 255), width=3)
    else:
        rng = np.random.default_rng(3)
        for j in range(9):
            x = c - 110 + rng.uniform(0, 220)
            y = c - 14 + rng.uniform(-6, 6)
            drip = 10 + 14 * prog(t, T_LOOK + 0.3 + j * 0.05, T_LOOK + 1.2)
            d.ellipse([x - 5, y, x + 5, y + drip], fill=(170, 10, 20, 255))
    m = Image.new("L", (sz, sz), 0)
    ImageDraw.Draw(m).ellipse([c - 150, c - 150, c + 150, c + 150], fill=255)
    spr.putalpha(Image.fromarray(np.minimum(np.asarray(spr.split()[3]), np.asarray(m))))
    ImageDraw.Draw(spr).ellipse([c - 150, c - 150, c + 150, c + 150], outline=ink, width=8)
    ImageDraw.Draw(spr).ellipse([c - 144, c - 144, c + 144, c + 144], outline=(250, 250, 252, 255), width=4)
    spr = spr.resize((2 * R + 20, 2 * R + 20), Image.LANCZOS)
    im.alpha_composite(spr, (int(cx - R - 10), int(cy - R - 10)))


def widget(d, x, y, label, value, col):
    d.rounded_rectangle([x, y, x + 240, y + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, x + 120, y + 10, label, font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
    spaced(d, x + 120, y + 38, value, font(MONO, 40), col + (255,), 1)


def sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    return cv.done()


BATH = CLINIC = None
FRAME0 = None


def panel(t, good):
    body, far = (GOOD_C, GOOD_FAR) if good else (LIE_C, LIE_FAR)
    if t < T_CUT:
        im = BATH.copy()
        pose, prop = bath_person(t, good)
        pts = AJ.place(pose, PERSON, 1, SC)
        spr, off = sprite(pts, body, far, 1)
        if good:
            im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
        im.alpha_composite(spr, off)
        d = ImageDraw.Draw(im)
        draw_brush(d, pts, prop, t)
        if not good and T_CRAM0 + 0.2 <= t < T_CUT:
            for j in range(5):
                x = SINK_X + 20 + j * 22
                if t > T_CRAM0 + 0.2 + j * 0.15:
                    d.ellipse([x - 5, FYP - 252, x + 5, FYP - 244], fill=(200, 20, 30, 255))
        n = flossed(t, good)
        if not (STRONG and t < 1.6):
                widget(d, 800, 100, "FLOSSED", f"{n}/30", (120, 230, 150) if good else (240, 120, 120) if n == 0 else
                   (240, 200, 120))
        OC.speech_at(im, t, BUB_GOOD if good else BUB_LIE, pts)
    else:
        im = CLINIC.copy()
        pts = AJ.place(PATIENT, CHAIR_HIP, 1, SC)
        spr, off = sprite(pts, body, far, 1)
        if good:
            im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
        im.alpha_composite(spr, off)
        dpose = DOC_LOOK if t >= T_LOOK else DOC
        dpts = AJ.place(dpose, (240, STAND_Y), 1, SC)
        dspr, doff = sprite(dpts, DOC_C, DOC_FAR, 1)
        im.alpha_composite(dspr, doff)
        d = ImageDraw.Draw(im)
        hx, hy = dpts["head"]
        d.rounded_rectangle([hx + 2, hy + 2, hx + 34, hy + 22], 5, fill=(230, 246, 250, 255), outline=INK + (255,),
                            width=2)
        d.ellipse([hx - 10, hy - 34, hx + 10, hy - 18], fill=(255, 240, 190, 255), outline=INK + (255,), width=2)
        hx2, hy2 = dpts["hl"]
        d.line([(hx2, hy2), (hx2 + 30, hy2 - 6)], fill=(200, 204, 214, 255), width=4)
        if not good and t >= T_VERDICT + 1.0:
            px, py = pts["head"]
            dy = 12 * prog(t, T_VERDICT + 1.0, T_VERDICT + 1.8)
            d.ellipse([px - 30, py - 40 + dy, px - 18, py - 22 + dy], fill=(140, 200, 255, 255), outline=INK + (255,))
        mouth_inset(im, t, good)
        OC.speech_at(im, t, [b for b in (BUB_GOOD if good else BUB_LIE) if b[0] >= T_CUT], pts)
        OC.speech_at(im, t, DOC_GOOD if good else DOC_LIE, dpts)
    # a soft cut to black and back
    k = 1 - abs(prog(t, T_CUT - 0.3, T_CUT + 0.3) * 2 - 1)
    if 0 < k:
        im.alpha_composite(Image.new("RGBA", im.size, (0, 0, 0, int(255 * k))))
    return im


def zoom(im, t, focus):
    if not STRONG:
        return im
    k = smooth(prog(t, 0.6, 1.8))
    z = lerp(1.32, 1.0, k)
    if z <= 1.001:
        return im
    fx, fy = focus
    cw, ch = W / z, PH / z
    x0 = clamp(fx - cw / 2, 0, W - cw)
    y0 = clamp(fy - ch / 2, 0, PH - ch)
    return im.resize((W, PH), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


def frame(t):
    img = Image.new("RGBA", (W, H), (5, 5, 7, 255))
    img.alpha_composite(zoom(panel(t, True), t, (470, 380)), (0, TOP_Y0))
    img.alpha_composite(zoom(panel(t, False), t, (470, 380)), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    if t < T_CUT:
        n = days_left(t)
        s = f"DENTIST IN {n} DAY{'S' if n > 1 else ''}"
    else:
        s = "DENTIST: TODAY"
    fc = font(BOLD, 56)
    tw = fc.getlength(s)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, STRIP_Y - 46, W / 2 + tw / 2 + 26, STRIP_Y + 46], 10,
                        fill=(16, 6, 6, 255), outline=(90, 24, 22, 255), width=3)
    g = Image.new("RGBA", (int(tw + 120), 160), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((60, 30), s, font=fc, fill=RED + (200,))
    g = g.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(g, (int(W / 2 - tw / 2 - 60), int(STRIP_Y - 66)))
    d = ImageDraw.Draw(img)
    d.text((W / 2 - tw / 2, STRIP_Y - 35), s, font=fc, fill=RED + (255,))
    fl = font("Inter-SemiBold.otf", 38)
    la = smooth(prog(t, 1.5, 1.9)) if STRONG else 1.0
    if la > 0.01:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        if t < T_L1:
            spaced(ld, W / 2, TOP_Y0 + 14, "FLOSSES", fl, (240, 242, 248, int(255 * la)), 10)
        spaced(ld, W / 2, BOT_Y0 + 14, "\"FLOSSES\"", fl, (220, 224, 232, int(255 * la)), 10)
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
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
    global BATH, CLINIC
    BATH, CLINIC = build_bath(), build_clinic()


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
    figure = [72, 76, 79, 76, 74, 77, 81, 77]
    chords = [[48, 52, 55], [45, 48, 52], [41, 45, 48], [43, 47, 50]]
    shifts = [0, -3, -7, -5]
    t_end = T_LOOK
    i, tt = 0, 0.0 if STRONG else 0.2
    while tt < t_end:
        b = int(tt / BAR) % 4
        g = (0.045 if STRONG else 0.03) + 0.05 * prog(tt, 0, t_end)
        mix_in(mus, OC.piano(midi(figure[i % 8] + shifts[b] - 12), 0.4, 0.5), tt, g, 0.25)
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
    # brushing (soft) and the cram (fast squeaks)
    for tk in np.arange(0.2, T_CUT - 0.3, 0.6):
        mix_in(fx, noise(0.2, int(tk * 100), lo=2000, hi=7000) * env(int(0.2 * SR), 0.02, 0.1), tk, 0.012, 0.0)
    for tk in np.arange(T_CRAM0, T_CRAM1, 0.09):
        mix_in(fx, tone(2600 + 300 * math.sin(tk * 9), 0.05, (1, 0.3), a=0.002, d=0.03), tk, 0.015, 0.3)
    # the cut: a clinic "ding"
    mix_in(fx, tone(1318, 0.6, (1, 0.3), a=0.003, d=0.35), T_CUT + 0.2, 0.05)
    mix_in(fx, tone(988, 0.8, (1, 0.3), a=0.003, d=0.45), T_CUT + 0.45, 0.05)
    # the close-up: a sparkle above, a low "uh-oh" below
    for j, f in enumerate((2093, 2637, 3136)):
        mix_in(fx, tone(f, 0.3, (1,), a=0.002, d=0.2), T_LOOK + 0.3 + 0.08 * j, 0.02, -0.4)
    mix_in(fx, tone(98, 0.9, (1, 0.5, 0.2), a=0.02, d=0.6), T_LOOK + 0.35, 0.12, 0.4)
    for k, m in enumerate((48, 55, 60, 64)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), 14.6, 0.05, (k - 1.5) * 0.4)
    for j, m in enumerate((76, 72, 67, 72)):
        mix_in(mus, OC.piano(midi(m), 1.3, 0.5), 15.0 + j * 0.5, 0.05, 0.2)
    for b0, b1, s, w in BUB_GOOD + BUB_LIE + DOC_GOOD:
        mix_in(fx, tone(700, 0.07, (1,), a=0.003, d=0.025), max(0.0, b0), 0.025)
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
    out = sys.argv[1] if len(sys.argv) > 1 else f"floss-{VARIANT}.mp4"
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
