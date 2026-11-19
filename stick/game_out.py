#!/usr/bin/env python3
"""GTA 6 IS OUT - doer vs overthinker, dark spotlight style, our own lines and ending (owner, 2026-11-19).

Same day the game comes out. The doer turns the TV off ("LATER.") and works at his laptop: clients, a second screen,
cash stacks; REAL BANK climbs to $250,000 by day 730. The overthinker plays: GAME CASH climbs to $999,999,999 while his
REAL BANK goes below zero, pizza boxes pile up and the FINAL NOTICE comes. Day 730: the doer sits on a sofa and finally
plays ("MY TURN."); two movers carry the overthinker's TV away ("...ONE MORE MISSION?").
"HE BEAT THE GAME. / LIFE BEAT HIM."  40.8 s (17 bars at 100 bpm), loops on itself.

    python3 stick/game_out.py out/game-out.mp4
    ONLY_FRAMES=1,2.6,8,14,20,26,31.5,33.5,38 python3 stick/game_out.py out/go.mp4
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scroller_reader import GOLD, INK, RED, clamp, midi, mix_in, out_back, out_cubic, prog, put, tone, write_wav  # noqa
from keep_trying import pose_from  # noqa
from motivation_bus import FM, get_bubble, mono_text  # noqa
from get_fit import draw_man  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BAR = 4 * 60 / BPM
DUR = 17 * BAR                      # 40.8 s
LANE_H = 948
FLOOR = 790
T0, TEND = 3.2, 30.0               # days run between these
DAYS = 730
KEYS = [(3.2, 1), (8.0, 14), (13.0, 60), (18.0, 180), (23.0, 400), (27.0, 600), (30.0, 730)]
T_TEXT = 35.2
T_LOOP = DUR - 0.5
WHITE_B = (244, 244, 240)
GREY = (168, 168, 168)
LINE1, LINE2 = "HE BEAT THE GAME.", "LIFE BEAT HIM."

DOER_SAYS = [(1.0, 2.0, "LET'S GO!"), (2.4, 3.6, "LATER."), (8.2, 10.0, "+$500."), (13.2, 15.0, "NEW CLIENT."),
             (18.2, 20.0, "HIRED 2 PEOPLE."), (23.2, 25.0, "WE'RE GROWING.")]
OVER_SAYS = [(1.0, 2.6, "LET'S GO!"), (4.0, 6.0, "ONE MORE HEIST."), (8.6, 10.6, "I'LL START SUNDAY."),
             (13.6, 15.6, "I'M A BOSS IN HERE."), (18.6, 20.6, "MONEY IS MONEY."), (23.6, 25.6, "ALMOST LEVEL 100.")]


def day_at(t):
    if t <= KEYS[0][0]:
        return 1
    for (ta, da), (tb, db) in zip(KEYS, KEYS[1:]):
        if t <= tb:
            p = (t - ta) / (tb - ta)
            return int(round(da + (db - da) * p))
    return DAYS


def doer_bank(d):
    return 0 if d <= 1 else int(round(250000 * (d / DAYS) ** 1.6 / 10) * 10)


def game_cash(d):
    return 0 if d <= 1 else int(999999999 * (d / DAYS) ** 1.15)


def over_bank(d):
    return 0 if d < 200 else -int(round(4800 * (d - 200) / (DAYS - 200) / 10) * 10)


def money(v):
    return ("-$" if v < 0 else "$") + f"{abs(v):,}"


# ---------------------------------------------------------------- the dark set
_bg = None


def lane_bg():
    global _bg
    if _bg is not None:
        return _bg
    yy, xx = np.mgrid[0:LANE_H, 0:W].astype(np.float32)
    img = np.zeros((LANE_H, W, 3), np.float32) + np.array([12, 12, 14], np.float32)
    lx, ly = 470, 210
    inside = (yy >= ly) & (yy <= FLOOR)
    depth = np.clip((yy - ly) / (FLOOR - ly), 0, 1)
    half = 36 + depth * 380
    light = np.where(inside, np.clip(1 - np.abs(xx - lx) / half, 0, 1) ** 1.6 * (0.5 + 0.35 * (1 - depth)), 0) * 0.55
    light += np.exp(-(((xx - lx) / 380) ** 2 + ((yy - FLOOR) / 30) ** 2)) * 0.8
    light += np.exp(-(((xx - lx) ** 2 + (yy - ly) ** 2) / (2 * 50 ** 2))) * 0.9
    img += light[..., None] * np.array([255, 212, 158], np.float32) / 255 * 105
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    d.line([(lx, 90), (lx, ly - 18)], fill=(60, 60, 62), width=4)
    d.polygon([(lx - 44, ly + 14), (lx + 44, ly + 14), (lx + 20, ly - 22), (lx - 20, ly - 22)], fill=(52, 52, 56))
    d.ellipse([lx - 12, ly + 6, lx + 12, ly + 26], fill=(255, 236, 200))
    d.line([(40, FLOOR), (W - 40, FLOOR)], fill=(80, 80, 86), width=3)
    _bg = im
    return im


def desk_and_chair(d, x=600):
    d.rectangle([x, FLOOR - 220, x + 360, FLOOR - 196], fill=(80, 60, 46), outline=INK, width=5)
    for lx in (x + 16, x + 330):
        d.rectangle([lx, FLOOR - 196, lx + 14, FLOOR], fill=(60, 46, 36), outline=INK, width=3)
    d.rounded_rectangle([330, FLOOR - 250, 380, FLOOR - 100], 14, fill=(50, 50, 56), outline=INK, width=5)   # chair back
    d.rectangle([340, FLOOR - 120, 520, FLOOR - 100], fill=(60, 60, 66), outline=INK, width=4)
    d.line([(430, FLOOR - 100), (430, FLOOR - 20)], fill=(40, 40, 44), width=10)
    d.line([(380, FLOOR - 10), (480, FLOOR - 10)], fill=(40, 40, 44), width=8)


def screen(d, x0, y0, w, h, kind, t, extra=None):
    d.rounded_rectangle([x0 - 8, y0 - 8, x0 + w + 8, y0 + h + 8], 10, fill=(28, 28, 32), outline=INK, width=5)
    if kind == "off":
        d.rectangle([x0, y0, x0 + w, y0 + h], fill=(10, 10, 12))
        return
    if kind == "gta":
        d.rectangle([x0, y0, x0 + w, y0 + h], fill=(40, 60, 120))
        for i in range(7):   # a little city skyline
            bx = x0 + 10 + i * (w - 20) / 7
            bh = 30 + (i * 37) % (h * 0.55)
            d.rectangle([bx, y0 + h - bh, bx + (w - 20) / 7 - 6, y0 + h], fill=(250, 120, 160) if i % 3 == 0 else (60, 200, 220))
        d.text((x0 + w / 2, y0 + h * 0.3), extra or "GTA 6", font=FM(int(h * 0.26)), fill=(255, 255, 255), anchor="mm")
        return
    if kind == "code":
        d.rectangle([x0, y0, x0 + w, y0 + h], fill=(18, 24, 30))
        for i in range(6):
            ln = 0.3 + 0.6 * abs(math.sin(i * 1.7 + int(t * 3)))
            d.line([(x0 + 12, y0 + 16 + i * (h - 24) / 6), (x0 + 12 + (w - 24) * ln, y0 + 16 + i * (h - 24) / 6)],
                   fill=(120, 220, 160) if i % 2 else (140, 180, 255), width=4)


def bubble(c, txt, x, y, p, a=1.0):
    b = get_bubble(txt)
    put(c, b, x + b.width * 0.22, y, 0.5 + 0.5 * out_back(clamp(p), 2.2), min(1, p * 2) * a)


def man(c, pose, x, y, body, face="calm", look=1, prop=None, s=0.78):
    spr, (ax, ay) = draw_man(pose, body, face, look, s, 0.0, prop)
    c.alpha_composite(spr, (int(x - ax), int(y - ay)))


SEATED = dict(lean=10, dy=70, tl=82, sl=-82, tr=76, sr=-78, al=62, bl=-36, ar=68, br=-42)


# ---------------------------------------------------------------- lanes
def doer_lane(t, day):
    c = lane_bg().copy()
    d = ImageDraw.Draw(c)
    if t >= TEND + 0.3:   # day 730: sofa, big TV, finally plays
        d.rounded_rectangle([250, FLOOR - 190, 640, FLOOR - 60], 30, fill=(150, 60, 50), outline=INK, width=6)
        d.rounded_rectangle([230, FLOOR - 120, 660, FLOOR - 40], 24, fill=(170, 70, 58), outline=INK, width=6)
        screen(d, 700, FLOOR - 470, 330, 210, "gta", t)
        d.rectangle([840, FLOOR - 252, 890, FLOOR], fill=(40, 40, 44), outline=INK, width=4)
        p = pose_from(lean=-10, **{k: v for k, v in SEATED.items() if k != "lean"})
        man(c, p, 440, FLOOR - 70, WHITE_B, "happy", 1)
        put(c, get_cash_stack(6), 130, FLOOR - 60)
        bubble(c, "MY TURN.", 420, 300, prog(t, TEND + 0.8, 0.25))
        return c
    desk_and_chair(d)
    if t < 2.4:
        screen(d, 690, FLOOR - 420, 260, 170, "gta", t, "GTA 6 IS OUT")
        d.rectangle([800, FLOOR - 242, 840, FLOOR - 220], fill=(40, 40, 44))
        p = pose_from(**SEATED)
    else:
        screen(d, 690, FLOOR - 420, 260, 170, "off" if day < 2 else "code", t)
        if day >= 60:   # a second screen
            d.rectangle([732, FLOOR - 432, 748, FLOOR - 236], fill=(40, 40, 44))
            screen(d, 640, FLOOR - 560, 200, 120, "code", t + 1.3)
        typing = math.sin(t * 18) * 6
        p = pose_from(**dict(SEATED, bl=-36 + typing, br=-42 - typing))
        # laptop on the desk
        d.polygon([(700, FLOOR - 222), (840, FLOOR - 222), (860, FLOOR - 236), (720, FLOOR - 236)], fill=(180, 180, 186), outline=INK)
    face = "happy" if day > 30 else "calm"
    man(c, p, 470, FLOOR - 40, WHITE_B, face, 1)
    stacks = 0 if day < 14 else min(6, 1 + day // 120)
    if stacks:
        put(c, get_cash_stack(stacks), 140, FLOOR - 60)
    if t >= 2.4 and day > 1 and (t * 1.6) % 1 < 0.45:   # notifications pop from the screen
        u = (t * 1.6) % 1 / 0.45
        put(c, mono_text("+$" + ("500" if day < 180 else "2,500"), 30, (120, 230, 150), 2), 820, FLOOR - 470 - u * 80, 1, 1 - u)
    for s_, e_, txt in DOER_SAYS:
        if s_ <= t < e_:
            bubble(c, txt, 300, 300, prog(t, s_, 0.25), 1 - prog(t, e_ - 0.2, 0.2))
    return c


_cash = {}


def get_cash_stack(n):
    if n in _cash:
        return _cash[n]
    im = Image.new("RGBA", (180, 60 + n * 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(n):
        y = im.height - 30 - i * 26
        d.rounded_rectangle([10, y - 22, 170, y + 2], 5, fill=(90, 190, 110), outline=INK, width=3)
        d.ellipse([78, y - 18, 102, y - 2], outline=(30, 110, 50), width=3)
    _cash[n] = im
    return im


def over_lane(t, day):
    c = lane_bg().copy()
    d = ImageDraw.Draw(c)
    desk_and_chair(d)
    gone = clamp((t - TEND - 1.0) / 1.6) if t >= TEND else 0.0
    # the TV (movers carry it off at the end)
    tv_x = 690 + gone * 700
    if gone < 1:
        screen(d, tv_x, FLOOR - 420, 260, 170, "gta", t, "$" + f"{game_cash(day):,}"[:11] if day > 1 else "GTA 6 IS OUT")
    if t >= TEND + 0.9:   # two grey movers
        for k, mx in enumerate((tv_x - 60, tv_x + 330)):
            mp = pose_from(lean=6, tl=25 * math.sin(t * 9 + k), sl=-30, tr=-25 * math.sin(t * 9 + k), sr=-30, al=110, bl=-30, ar=110, br=-30)
            man(c, mp, mx, FLOOR, (110, 110, 116), "calm", -1)
    # pizza boxes and cans pile up
    boxes = 0 if day < 10 else min(8, 1 + day // 90)
    for i in range(boxes):
        d.rectangle([90 - (i % 2) * 6, FLOOR - 30 - i * 28, 250 - (i % 2) * 6, FLOOR - 4 - i * 28], fill=(210, 160, 100), outline=INK, width=3)
        d.text((170 - (i % 2) * 6, FLOOR - 17 - i * 28), "PIZZA", font=FM(16), fill=(150, 50, 40), anchor="mm")
    if day >= 300:   # the FINAL NOTICE on the wall
        a = prog(day, 300, 40)
        d.rectangle([120, 280, 280, 400], fill=(250, 246, 236), outline=INK, width=4)
        d.text((200, 315), "FINAL", font=FM(26), fill=RED, anchor="mm")
        d.text((200, 355), "NOTICE", font=FM(26), fill=RED, anchor="mm")
    if t < 2.4 or gone < 1 or True:
        controller_y = 0
    p = pose_from(**SEATED)
    face = "o" if t >= TEND + 1.0 else ("happy" if day < 300 else "calm")
    man(c, p, 470, FLOOR - 40, GREY, face, 1)
    if t >= TEND + 1.0:   # the controller, cable hanging loose
        hx, hy = 470 + p["hr"][0] * 0.78, FLOOR - 40 + p["hr"][1] * 0.78
        d.rounded_rectangle([hx - 20, hy - 12, hx + 24, hy + 12], 8, fill=(40, 40, 46), outline=INK, width=3)
        d.line([(hx + 24, hy), (hx + 80, hy + 40), (hx + 110, hy + 120)], fill=(30, 30, 34), width=4)
        bubble(c, "...ONE MORE MISSION?", 330, 300, prog(t, TEND + 2.6, 0.25))
    else:
        for s_, e_, txt in OVER_SAYS:
            if s_ <= t < e_:
                bubble(c, txt, 330, 300, prog(t, s_, 0.25), 1 - prog(t, e_ - 0.2, 0.2))
        if day > 1 and (t * 1.4) % 1 < 0.4:
            u = (t * 1.4) % 1 / 0.4
            put(c, mono_text("MISSION PASSED", 24, GOLD, 2), 820, FLOOR - 470 - u * 70, 1, 1 - u)
    return c


# ---------------------------------------------------------------- frame
def counters(c, y0, label, label_col, bank, game):
    put(c, mono_text(label, 34, label_col, 8), W / 2, y0 + 50)
    put(c, mono_text("REAL BANK", 24, (190, 190, 190), 4), 200, y0 + 104)
    put(c, mono_text(money(bank), 48, (120, 230, 150) if bank > 0 else (RED if bank < 0 else (160, 160, 160))), 200, y0 + 152)
    put(c, mono_text("GAME CASH", 24, (190, 190, 190), 4), W - 210, y0 + 104)
    put(c, mono_text(money(game), 40 if game > 99999999 else 48, GOLD if game else (160, 160, 160)), W - 210, y0 + 152)


def frame_raw(t):
    day = day_at(t)
    c = Image.new("RGBA", (W, H), (10, 10, 12, 255))
    c.alpha_composite(doer_lane(t, day), (0, 0))
    c.alpha_composite(over_lane(t, day), (0, 972))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 948, W, 972], fill=(6, 6, 7))
    d.line([(0, 948), (W, 948)], fill=(58, 58, 62), width=2)
    d.line([(0, 972), (W, 972)], fill=(58, 58, 62), width=2)
    counters(c, 0, "DOER", GOLD, doer_bank(day), 0)
    counters(c, 972 + 30, "OVERTHINKER", (190, 190, 190), over_bank(day), game_cash(day))
    pw, ph = 380, 86
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([0, 0, pw - 1, ph - 1], 43, fill=(20, 20, 24, 245), outline=(255, 255, 255), width=3)
    dd.text((pw / 2, 24), "SAME GAME", font=FM(22), fill=(190, 190, 190), anchor="mm")
    dd.text((pw / 2, 58), f"DAY {day}", font=FM(38), fill=(255, 255, 255), anchor="mm")
    put(c, im, W / 2, 960)
    if t >= T_TEXT:
        p = out_cubic(prog(t, T_TEXT, 0.4))
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(170 * p))))
        chars = int((t - T_TEXT - 0.3) / 0.06)
        l1 = LINE1[:max(0, chars)]
        l2 = LINE2[:max(0, chars - len(LINE1) - 4)]
        cur = "_" if int(t * 3) % 2 == 0 else " "
        if l1:
            im = mono_text(l1 + (cur if not l2 else ""), 64, (245, 245, 240), 2)
            c.alpha_composite(im, (int(W / 2 - mono_text(LINE1, 64, spacing=2).width / 2), 840))
        if l2:
            im = mono_text(l2 + cur, 64, GOLD, 2)
            c.alpha_composite(im, (int(W / 2 - mono_text(LINE2, 64, spacing=2).width / 2), 930))
    return c


def frame(t):
    c = frame_raw(t)
    if t >= T_LOOP:
        c = Image.blend(c, frame_raw(0.0), out_cubic(prog(t, T_LOOP, DUR - T_LOOP)))
    return c.convert("RGB")


# ---------------------------------------------------------------- audio
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    beat = 60 / BPM
    chords = [[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 55]]
    roots = [33, 29, 31, 28]
    for b in range(17):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        grow = clamp((t0 - T0) / (TEND - T0))
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), BAR + 0.05, (1, 0.45, 0.2, 0.06), a=0.03, d=1.2), t0, 0.045 + 0.02 * grow, (k - 1.5) * 0.35)
        for q in range(4):
            tb = t0 + q * beat
            mix_in(mus, tone(110, 0.3, (1,), a=0.002, d=0.1, sweep=42), tb, 0.5 + 0.2 * grow if q % 2 == 0 else 0.32)
            mix_in(mus, tone(midi(rt), beat * 0.45, (1, 0.5, 0.15), a=0.004, d=0.13), tb, 0.22)
            if q % 2 == 1:
                mix_in(mus, tone(330, 0.16, (1, 0.6, 0.45, 0.3, 0.2), a=0.002, d=0.04, sweep=190), tb, 0.12)
            for e in range(2):
                mix_in(mus, tone(3000, 0.03, (1,), a=0.0008, d=0.006), tb + e * beat / 2, 0.03, 0.4 - 0.8 * e)
            m = ch[(q + b) % 4] + 12
            mix_in(mus, tone(midi(m), 0.3, (1, 0.3, 0.1), a=0.003, d=0.1), tb + beat * 0.75, 0.05 + 0.02 * grow, 0.2)
    # TV click off for the doer
    mix_in(fx, tone(1200, 0.06, (1, 0.5), a=0.001, d=0.015), 2.45, 0.15, -0.3)
    mix_in(fx, tone(300, 0.25, (1,), a=0.002, d=0.08, sweep=80), 2.47, 0.12, -0.3)
    # notifications: a coin for the doer, a game jingle for the overthinker
    t = T0
    while t < TEND:
        mix_in(fx, tone(2200, 0.08, (1, 0.3), a=0.001, d=0.03), t, 0.04, -0.4)
        t += 1 / 1.6
    t = T0 + 0.3
    while t < TEND:
        mix_in(fx, tone(midi(79), 0.12, (1, 0.5), a=0.002, d=0.05), t, 0.03, 0.4)
        mix_in(fx, tone(midi(84), 0.12, (1, 0.5), a=0.002, d=0.05), t + 0.06, 0.03, 0.4)
        t += 1 / 1.4
    for s_, _, _ in DOER_SAYS + OVER_SAYS:
        mix_in(fx, tone(560, 0.11, (1, 0.3), a=0.002, d=0.05, sweep=1100), s_, 0.08)
    # day 730: the doer's TV turns on, then the movers - heavy steps and a low "dun dun"
    for k, m in enumerate([60, 64, 67, 72]):
        mix_in(fx, tone(midi(m), 1.4, (1, 0.35, 0.12), a=0.01, d=0.7), TEND + 0.3 + k * 0.07, 0.07, -0.3)
    for k in range(6):
        mix_in(fx, tone(70, 0.25, (1, 0.5), a=0.002, d=0.07, sweep=45), TEND + 1.0 + k * 0.33, 0.25, 0.3)
    for k, (m, d_) in enumerate([(38, 0.5), (37, 1.0)]):
        mix_in(fx, tone(midi(m), d_ + 0.4, (1, 0.6, 0.4, 0.25), a=0.005, d=0.5), TEND + 2.6 + k * 0.35, 0.25, 0.3)
    total = len(LINE1) + 4 + len(LINE2)
    for i in range(total):
        if (LINE1 + "    " + LINE2)[i] != " ":
            mix_in(fx, tone(1700 + (i % 3) * 140, 0.025, (1, 0.4), a=0.0006, d=0.005), T_TEXT + 0.3 + i * 0.06, 0.05)
    x = mus + fx
    x -= x.mean(axis=0)
    x = np.tanh(x * 1.3)
    x *= 0.89 / np.abs(x).max()
    r = int(0.005 * SR)
    x[:r] *= np.linspace(0, 1, r)[:, None]
    x[-r:] *= np.linspace(1, 0, r)[:, None]
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "out/game-out.mp4"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    only = os.environ.get("ONLY_FRAMES")
    if only:
        for s in only.split(","):
            frame(float(s)).save(f"{out[:-4]}-{float(s):05.2f}.png")
        return
    wav = out[:-4] + ".wav"
    write_wav(wav, audio())
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                           out], stdin=subprocess.PIPE)
    for i in range(int(round(DUR * FPS))):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg failed")
    os.remove(wav)
    print("wrote", out)


if __name__ == "__main__":
    main()
