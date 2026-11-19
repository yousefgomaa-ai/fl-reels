#!/usr/bin/env python3
"""IDEAS.md #5 - "JUST ONE EPISODE". Split screen: THE PLAN above, REALITY below, 18 s, loops on itself.

23:00, the same bed, the same laptop: "JUST ONE EPISODE." Above, the plan: one episode, the laptop closes, asleep
by 23:45. Below, reality: "NEXT EPISODE IN 5..." - "OK ONE MORE." - EPISODE 2, 3, 4 ("THIS ONE IS SHORT."), 5, 6
("WAIT, WHAT?!"), 7, 8 ("LAST ONE. FOR REAL."); snack wrappers pile up on the blanket, the window goes from night to
sunrise, the red clock runs to 07:00 - and the alarm rings. "...ALREADY?"
"ONE EPISODE IS A LIE / WE TELL OURSELVES."  FOLLOW FOR MORE.

    python3 stick/one_episode.py stick/one-episode.mp4
    ONLY_FRAMES=0.6,3.0,4.4,6.6,9.6,11.4,12.9,14.0,15.8 python3 stick/one_episode.py /tmp/oe
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
PLAN, PLAN_FAR = AJ.DOER, AJ.DOER_FAR
REAL, REAL_FAR = AJ.OT, AJ.OT_FAR
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP

BED = (110, 700)
MATT = FYP - 150                          # mattress top
HIP = (230, MATT - 10)
STAND_X = 760                             # nightstand
WIN = (380, 70, 640, 290)

# ---------------------------------------------------------------- timeline
T_EP1_END = 4.0
EPISODES = [1.6, 4.8, 6.4, 7.8, 9.0, 10.0, 10.9, 11.7]   # when each starts (below)
T_CLOCK0, T_CLOCK1 = 1.6, 12.6            # 23:00 -> 07:00
T_ALARM = 12.6
T_PLAN_CLOSE, T_PLAN_SLEEP = 4.1, 4.7
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "ONE EPISODE IS A LIE", "WE TELL OURSELVES."
T_FOLLOW = 16.95

BUB_BOTH = [(0.3, 1.6, "JUST ONE EPISODE.", "me")]
BUB_REAL = [(4.25, 5.4, "OK. ONE MORE.", "me"), (7.0, 8.0, "THIS ONE IS SHORT.", "me"), (9.4, 10.3, "WAIT, WHAT?!", "me"),
            (11.0, 11.9, "LAST ONE. FOR REAL.", "me"), (13.1, 14.7, "...ALREADY?", "me")]


def clock_minutes(t):
    return int(23 * 60 + 480 * prog(t, T_CLOCK0, T_CLOCK1) ** 1.2) % 1440


def episode(t):
    n = 1
    for i, s in enumerate(EPISODES):
        if t >= s:
            n = i + 1
    return n


def dawn(t):
    return smooth(prog(t, 9.6, 12.6))


# ---------------------------------------------------------------- poses
SIT_BED = {"head": (14, -148), "neck": (8, -106), "el": (30, -60), "hl": (58, -46), "er": (26, -56), "hr": (54, -42),
           "kl": (60, -10), "fl": (120, -4), "kr": (60, -4), "fr": (120, 2)}
SIT_SNACK = dict(SIT_BED, er=(30, -100), hr=(16, -134))
SIT_SHOCK = dict(SIT_BED, head=(6, -152), el=(10, -110), hl=(-6, -150), er=(20, -110), hr=(4, -150))
SLUMP = dict(SIT_BED, head=(30, -132), neck=(20, -96))
LIE = {"head": (-110, -30), "neck": (-70, -24), "el": (-40, -50), "hl": (-20, -30), "er": (-44, -46), "hr": (-24, -26),
       "kl": (60, -8), "fl": (120, -4), "kr": (60, -2), "fr": (120, 2)}


def person(t, plan):
    if plan:
        if t < T_PLAN_CLOSE:
            return SIT_BED, HIP, "laptop"
        k = smooth(prog(t, T_PLAN_CLOSE, T_PLAN_SLEEP))
        return lerp_pose(SIT_BED, LIE, k), (lerp(HIP[0], 330, k), lerp(HIP[1], MATT - 4, k)), ("sleep" if t > T_PLAN_SLEEP + 0.3 else None)
    if 9.4 <= t < 10.3:
        return SIT_SHOCK, HIP, "laptop"
    if t >= T_ALARM:
        k = smooth(prog(t, T_ALARM, T_ALARM + 0.3))
        return lerp_pose(SLUMP, SIT_SHOCK, 0.4 * k), HIP, "laptop"
    if int(t * 1.3) % 3 == 1 and t > 2.5:
        k = 0.5 + 0.5 * math.sin(t * 6)
        return lerp_pose(SIT_BED, SIT_SNACK, k), HIP, "laptop"
    return lerp_pose(SIT_BED, SLUMP, smooth(prog(t, 5.0, 12.0))), HIP, "laptop"


# ---------------------------------------------------------------- the bedroom
def build_room():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + 8
    img = np.where((yy > FYP)[..., None], img * 0.8 + 8, img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(46, 44, 44, 255), width=2)
    x0, x1 = BED
    d.rounded_rectangle([x0 - 30, FYP - 330, x0 + 6, FYP], 10, fill=(84, 66, 52, 255), outline=ink, width=4)
    d.rounded_rectangle([x0, MATT, x1, MATT + 70], 12, fill=(222, 222, 228, 255), outline=ink, width=4)
    d.rectangle([x0, MATT + 70, x1, FYP - 30], fill=(84, 66, 52, 255), outline=ink, width=4)
    for lx in (x0 + 10, x1 - 22):
        d.rectangle([lx, FYP - 30, lx + 12, FYP], fill=(60, 48, 40, 255))
    d.rounded_rectangle([x0 + 6, MATT - 60, x0 + 110, MATT + 6], 18, fill=(240, 240, 244, 255), outline=ink, width=3)
    # nightstand
    d.rectangle([STAND_X, FYP - 160, STAND_X + 130, FYP], fill=(100, 76, 56, 255), outline=ink, width=4)
    d.rectangle([STAND_X + 12, FYP - 140, STAND_X + 118, FYP - 90], outline=ink, width=3)
    return im


def draw_window(d, t, plan):
    x0, y0, x1, y1 = WIN
    k = 0.0 if plan else dawn(t)
    top = PW.lerp_c((10, 14, 34), (110, 150, 210), k)
    bot = PW.lerp_c((24, 30, 60), (255, 190, 120), k)
    for i in range(y1 - y0):
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=PW.lerp_c(top, bot, i / (y1 - y0)) + (255,))
    if k > 0.2:
        r = 34
        cy = lerp(y1 + 20, y1 - 70, k)
        d.ellipse([x0 + 160 - r, cy - r, x0 + 160 + r, cy + r], fill=(255, 220, 120, int(255 * k)))
    else:
        d.ellipse([x1 - 70, y0 + 24, x1 - 40, y0 + 54], fill=(240, 238, 220, 255))
    for i in range(6):
        bx = x0 + 6 + i * 46
        bh = 40 + (i * 37) % 60
        d.rectangle([bx, y1 - bh, bx + 40, y1], fill=PW.lerp_c((14, 16, 28), (60, 50, 60), k) + (255,))
    ink = INK + (255,)
    d.rectangle([x0, y0, x1, y1], outline=ink, width=8)
    d.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=ink, width=6)


def draw_alarm(d, t, plan):
    ink = INK + (255,)
    ring = (not plan) and t >= T_ALARM
    sh = 5 * math.sin(t * 60) if ring else 0
    cx, cy = STAND_X + 66 + sh, FYP - 196
    d.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=(220, 70, 60, 255), outline=ink, width=4)
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(250, 248, 240, 255))
    for s in (-1, 1):
        d.ellipse([cx + s * 30 - 12, cy - 50, cx + s * 30 + 12, cy - 30], fill=(220, 70, 60, 255), outline=ink, width=3)
    d.line([(cx, cy), (cx, cy - 18)], fill=ink, width=4)
    d.line([(cx, cy), (cx + 14, cy + 4)], fill=ink, width=4)
    if ring:
        for j in range(3):
            r = 50 + 16 * j + 10 * math.sin(t * 20)
            d.arc([cx - r, cy - r, cx + r, cy + r], 200, 250, fill=(250, 250, 250, 255), width=4)
            d.arc([cx - r, cy - r, cx + r, cy + r], 290, 340, fill=(250, 250, 250, 255), width=4)


def draw_laptop(im, d, pts, t, plan, closed=False):
    ink = INK + (255,)
    x = pts["hip"][0] + 140
    y = MATT - 14
    if closed:
        d.rounded_rectangle([STAND_X + 10, FYP - 172, STAND_X + 120, FYP - 160], 3, fill=(130, 134, 144, 255), outline=ink,
                            width=2)
        return
    d.rounded_rectangle([x - 60, y - 8, x + 60, y + 2], 3, fill=(130, 134, 144, 255), outline=ink, width=2)
    d.polygon([(x + 56, y - 6), (x + 76, y - 120), (x + 90, y - 120), (x + 70, y - 4)], fill=(130, 134, 144, 255),
              outline=ink)
    # the light of the screen on him
    g = Image.new("RGBA", (400, 360), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([60, 60, 340, 300], fill=(120, 170, 255, 70))
    g = g.filter(ImageFilter.GaussianBlur(40))
    im.alpha_composite(g, (int(x - 160), int(y - 260)))


def draw_screen_card(d, t, plan):
    """A big card at the right of the panel: what is on the laptop."""
    x0, y0 = 760, 330
    ink = INK + (255,)
    if plan and t >= T_PLAN_CLOSE:
        return
    d.rounded_rectangle([x0, y0 - 220, x0 + 290, y0 - 50], 14, fill=(16, 18, 26, 240), outline=(110, 114, 130, 255), width=3)
    if (not plan) and T_EP1_END <= t < EPISODES[1]:
        n = 5 - int((t - T_EP1_END) / (EPISODES[1] - T_EP1_END) * 5)
        spaced(d, x0 + 145, y0 - 190, "NEXT EPISODE IN", font("Inter-SemiBold.otf", 22), (220, 220, 230, 255), 2)
        spaced(d, x0 + 145, y0 - 160, str(max(1, n)), font(BOLD, 60), (255, 255, 255, 255), 0)
        return
    ep = 1 if plan else episode(t)
    start = EPISODES[ep - 1] if not plan else 1.6
    end = (EPISODES[ep] if ep < len(EPISODES) else T_ALARM + 0.8) if not plan else T_EP1_END
    p = prog(t, start, end)
    spaced(d, x0 + 145, y0 - 200, f"EPISODE {ep}", font(BOLD, 40), (255, 255, 255, 255), 2)
    d.rounded_rectangle([x0 + 20, y0 - 110, x0 + 270, y0 - 96], 6, fill=(60, 62, 72, 255))
    d.rounded_rectangle([x0 + 20, y0 - 110, x0 + 20 + 250 * p, y0 - 96], 6, fill=(229, 9, 20, 255))


def person_sprite(pts, body, far):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, 1)
    return cv.done()


def blanket(d, pts):
    ink = INK + (255,)
    hx, hy = pts["hip"]
    d.rounded_rectangle([hx - 30, MATT - 40, BED[1] - 6, MATT + 50], 22, fill=(96, 110, 150, 255), outline=ink, width=4)


def wrappers(d, t):
    rng = np.random.default_rng(5)
    n = int(clamp((t - 3.0) / 9.0) * 9)
    for i in range(n):
        x = 420 + rng.uniform(0, 240)
        y = MATT - 36 + rng.uniform(-6, 10)
        col = [(230, 80, 60), (240, 200, 60), (80, 160, 220)][i % 3]
        d.polygon([(x - 18, y - 8), (x + 16, y - 12), (x + 20, y + 6), (x - 14, y + 10)], fill=col + (255,),
                  outline=INK + (255,))


ROOM = None
FRAME0 = None


def panel(t, plan):
    im = ROOM.copy()
    d = ImageDraw.Draw(im)
    draw_window(d, t, plan)
    draw_alarm(d, t, plan)
    pose, hip, prop = person(t, plan)
    pts = AJ.place(pose, hip, 1, SC)
    body, far = (PLAN, PLAN_FAR) if plan else (REAL, REAL_FAR)
    spr, off = person_sprite(pts, body, far)
    if plan:
        im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    blanket(d, pts)
    if not plan:
        wrappers(d, t)
    if prop == "laptop":
        draw_laptop(im, d, pts, t, plan)
    elif plan:
        draw_laptop(im, d, pts, t, plan, closed=True)
    d = ImageDraw.Draw(im)
    draw_screen_card(d, t, plan)
    if prop == "sleep":
        for i in range(2):
            ph = (t * 0.7 + i * 0.5) % 1.0
            hx, hy = pts["head"]
            d.text((hx + 20 + 26 * ph + i * 12, hy - 60 - 50 * ph), "z", font=font("Inter-Bold.otf", 26 + 8 * i),
                   fill=(220, 226, 240, int(255 * math.sin(math.pi * ph))))
    if plan and t >= T_PLAN_SLEEP:
        bx, by = 760, 110
        d.rounded_rectangle([bx, by, bx + 290, by + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
        spaced(d, bx + 145, by + 10, "ASLEEP AT", font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
        spaced(d, bx + 145, by + 38, "23:45", font(MONO, 40), (120, 230, 150, 255), 1)
    if not plan and int(t * 2) % 2 == 0 and t > 8:
        # red, tired eyes
        hx, hy = pts["head"]
        d.ellipse([hx + 8, hy - 10, hx + 16, hy - 2], fill=(230, 60, 60, 255))
        d.ellipse([hx + 22, hy - 10, hx + 30, hy - 2], fill=(230, 60, 60, 255))
    OC.speech_at(im, t, BUB_BOTH + ([] if plan else BUB_REAL), pts)
    return im


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
        spaced(d, W / 2, TOP_Y0 + 14, "THE PLAN", fl, (240, 242, 248, 255), 10)
    spaced(d, W / 2, BOT_Y0 + 14, "REALITY", fl, (220, 224, 232, 255), 10)
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


def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    eighth = BEAT / 2
    figure = [72, 76, 79, 76, 74, 77, 81, 77]
    chords = [[48, 52, 55], [45, 48, 52], [41, 45, 48], [43, 47, 50]]
    shifts = [0, -3, -7, -5]
    t_end = T_ALARM
    i, tt = 0, 0.2
    while tt < t_end:
        b = int(tt / BAR) % 4
        g = 0.03 + 0.05 * prog(tt, 0, t_end)
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
    # each new episode: the streaming "ta-dum"
    for s in EPISODES[1:]:
        mix_in(fx, tone(98, 0.25, (1, 0.5), a=0.003, d=0.1), s, 0.12, 0.3)
        mix_in(fx, tone(73, 0.6, (1, 0.5), a=0.003, d=0.3), s + 0.22, 0.14, 0.3)
    # the countdown beeps; snacks; the alarm
    for j in range(5):
        mix_in(fx, tone(880, 0.06, (1,), a=0.002, d=0.02), T_EP1_END + j * 0.16, 0.03, 0.3)
    for tk in np.arange(3.0, 12.0, 1.3):
        mix_in(fx, noise(0.12, int(tk * 100), lo=1500, hi=6000) * env(int(0.12 * SR), 0.002, 0.03), tk, 0.04, 0.3)
    for j in range(8):
        mix_in(fx, tone(1300, 0.09, (1, 0.5, 0.3), a=0.001, d=0.05), T_ALARM + j * 0.13, 0.08, 0.3)
        mix_in(fx, tone(1300, 0.09, (1, 0.5, 0.3), a=0.001, d=0.05), T_ALARM + 1.3 + j * 0.13, 0.06, 0.3)
    # morning: a soft chord for the line
    for k, m in enumerate((48, 55, 60, 64)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), 14.6, 0.05, (k - 1.5) * 0.4)
    for j, m in enumerate((76, 72, 67, 72)):
        mix_in(mus, OC.piano(midi(m), 1.3, 0.5), 15.0 + j * 0.5, 0.05, 0.2)
    for b0, b1, s, w in BUB_BOTH + BUB_REAL:
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
    out = sys.argv[1] if len(sys.argv) > 1 else "one-episode.mp4"
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
