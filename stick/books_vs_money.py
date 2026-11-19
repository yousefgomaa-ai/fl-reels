#!/usr/bin/env python3
"""BOOK SMART vs RICH KID - four obstacles, the rich kid buys his way past every one; the twist: the book-smart one
finally gets a job... and the boss is the rich kid. 26.4 s (7 bars at 100 bpm), loops on itself.

Two lanes (book smart on top, rich kid below) with a scoreboard between them. Each obstacle is its own little set
that slides in. 1080x1920, PIL + numpy, music and sounds synthesised from sines (no samples, no noise).

    python3 stick/books_vs_money.py out/books-vs-money.mp4
    ONLY_FRAMES=1.2,3.7,6.2,8.7,11.5,12.6,15.5 python3 stick/books_vs_money.py out/b.mp4
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scroller_reader import BLACK, GOLD, INK, clamp, midi, mix_in, out_back, out_cubic, prog, put, tone, write_wav  # noqa
from keep_trying import pose_from  # noqa
from motivation_bus import FM, WHITE_B, draw_stick, get_bubble, mono_text  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BAR = 4 * 60 / BPM
DUR = 11 * BAR                                   # 26.4 s
V = 3.8                                          # one obstacle
TS = 2.5 / V                                     # the obstacles' moves were timed for 2.5 s; slowed to V
TS2 = 0.7                                        # the twist, slowed the same way
SLIDE = 0.28
T_TWIST = 4 * V                                  # 15.2
T_TEXT = T_TWIST + 3.2 / TS2                     # 19.8
T_LOOP = DUR - 0.45
LANE_H = 948
LANES = {"book": 0, "rich": 972}
FLOOR = 790                                      # inside a lane
S = 0.72                                         # stickman scale in the lanes
OBST = ["LOCKED DOOR", "RIVER", "WALL", "JOB INTERVIEW"]
GREEN = (90, 190, 110)
LINE1, LINE2 = "HE STUDIED HOW TO PASS.", "THE OTHER ONE OWNED THE ROAD."


def vig_at(t):
    return min(3, int(t // V)), (t % V) if t < T_TWIST else V


# ---------------------------------------------------------------- small drawing helpers
def at(pose, key, x, y, s=S):
    px, py = pose[key]
    return x + px * s, y + py * s


def stick(c, pose, x, y, face="calm", look=1, s=S, body=WHITE_B, who=None, alpha=1.0):
    spr, anc = draw_stick(pose, body, face, look, s)
    if alpha < 0.999:
        spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
    sh = Image.new("RGBA", (150, 34), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([0, 0, 150, 34], fill=(0, 0, 0, int(70 * alpha)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), (int(x - 75), int(y - 14)))
    c.alpha_composite(spr, (int(x - anc[0]), int(y - anc[1])))
    d = ImageDraw.Draw(c)
    hx, hy = at(pose, "head", x, y, s)
    r = 52 * s
    if who == "book":      # round glasses
        for dx in (0.12, 0.48):
            ex = hx + look * r * 0.30 - (r * 0.18 if look < 0 else 0) + dx * r - r * 0.12
            d.ellipse([ex - r * 0.2, hy - r * 0.25, ex + r * 0.2, hy + r * 0.15], outline=INK, width=4)
    if who == "rich":      # sunglasses + gold chain
        ex = hx + look * r * 0.30 - (r * 0.18 if look < 0 else 0)
        d.rounded_rectangle([ex - r * 0.28, hy - r * 0.2, ex + r * 0.64, hy + r * 0.12], 6, fill=INK)
        nx, ny = at(pose, "neck", x, y, s)
        d.arc([nx - 26, ny - 20, nx + 26, ny + 26], 20, 160, fill=GOLD, width=6)


def bubble_at(c, txt, x, y, p=1.0, a=1.0):
    b = get_bubble(txt)
    put(c, b, x + b.width * 0.22, y, 0.5 + 0.5 * out_back(clamp(p), 2.2), min(1, p * 2) * a)


def cash(d, x, y, sc=1.0):
    d.rounded_rectangle([x - 34 * sc, y - 18 * sc, x + 34 * sc, y + 18 * sc], 5, fill=GREEN, outline=INK, width=4)
    d.ellipse([x - 9 * sc, y - 9 * sc, x + 9 * sc, y + 9 * sc], outline=(30, 110, 50), width=3)


def book(d, x, y, col=(200, 70, 60)):
    d.polygon([(x - 34, y - 26), (x, y - 20), (x + 34, y - 26), (x + 34, y + 20), (x, y + 26), (x - 34, y + 20)], fill=(250, 246, 232), outline=INK)
    d.line([(x, y - 20), (x, y + 26)], fill=INK, width=3)
    d.rectangle([x - 36, y + 20, x + 36, y + 28], fill=col, outline=INK)


# ---------------------------------------------------------------- sets (one lane, 1080 x 948)
def sky(top, bot):
    g = np.linspace(0, 1, LANE_H)[:, None, None]
    a = np.array(top, np.float32) * (1 - g) + np.array(bot, np.float32) * g
    return Image.fromarray(np.repeat(a, W, axis=1).astype(np.uint8), "RGB").convert("RGBA")


_sets = {}


def set_bg(i):
    if i in _sets:
        return _sets[i]
    if i == 0:      # street wall with a door
        im = sky((86, 74, 70), (150, 120, 100))
        d = ImageDraw.Draw(im)
        for y in range(0, FLOOR, 46):          # bricks
            for x in range((y // 46) % 2 * -60, W, 120):
                d.rectangle([x, y, x + 116, y + 42], fill=(156, 92, 70), outline=(120, 68, 52), width=3)
        d.rectangle([0, FLOOR, W, LANE_H], fill=(110, 110, 116))
    elif i == 1:    # river between two banks
        im = sky((130, 190, 230), (200, 230, 245))
        d = ImageDraw.Draw(im)
        d.ellipse([-200, FLOOR - 260, 700, FLOOR + 200], fill=(150, 200, 140))
        d.ellipse([500, FLOOR - 300, 1400, FLOOR + 200], fill=(130, 186, 124))
        d.rectangle([0, FLOOR, W, LANE_H], fill=(116, 170, 96))
        d.rectangle([430, FLOOR - 6, 1010, LANE_H], fill=(70, 140, 210))
        for k in range(6):
            yy = FLOOR + 30 + k * 26
            d.line([(450 + (k * 37) % 90, yy), (520 + (k * 37) % 90, yy)], fill=(190, 225, 250), width=4)
    elif i == 2:    # tall wall at sunset
        im = sky((250, 170, 120), (255, 214, 160))
        d = ImageDraw.Draw(im)
        d.ellipse([760, 140, 920, 300], fill=(255, 236, 170))
        d.rectangle([0, FLOOR, W, LANE_H], fill=(150, 130, 110))
        d.rectangle([600, 120, 760, FLOOR], fill=(150, 150, 156), outline=INK, width=6)
        for y in range(160, FLOOR, 70):
            d.line([(600, y), (760, y)], fill=(120, 120, 126), width=3)
    else:           # office, interview desk
        im = sky((226, 228, 232), (204, 208, 214))
        d = ImageDraw.Draw(im)
        d.rectangle([680, 150, 960, 420], fill=(170, 210, 240), outline=(120, 124, 130), width=8)
        d.line([(820, 150), (820, 420)], fill=(120, 124, 130), width=6)
        d.rectangle([0, FLOOR, W, LANE_H], fill=(150, 120, 96))
    _sets[i] = im
    return im


def desk(d, x0=560):
    d.rectangle([x0, FLOOR - 170, x0 + 330, FLOOR - 140], fill=(120, 86, 60), outline=INK, width=5)
    d.rectangle([x0 + 20, FLOOR - 140, x0 + 310, FLOOR], fill=(104, 74, 52), outline=INK, width=5)


# ---------------------------------------------------------------- one obstacle in one lane
def lane(i, who, u):
    """The set of obstacle i for 'book' or 'rich' at local time u (0..V)."""
    c = set_bg(i).copy()
    d = ImageDraw.Draw(c)
    walk = lambda ph: pose_from(lean=10, tl=30 * math.sin(ph), sl=-30, tr=-30 * math.sin(ph), sr=-30, al=-25 * math.sin(ph), bl=40, ar=25 * math.sin(ph), br=40)
    stand = pose_from(lean=2, dy=math.sin(u * 3) * 2)
    x0 = 230
    if i == 0:   # LOCKED DOOR
        open_ = clamp((u - 1.0) / 0.35) if who == "rich" else 0.0
        dw = 190 * (1 - open_ * 0.82)
        d.rectangle([600, FLOOR - 380, 800, FLOOR], fill=(40, 30, 26))
        d.rectangle([600, FLOOR - 380, 600 + dw, FLOOR], fill=(110, 72, 46), outline=INK, width=6)
        if dw > 60:
            d.ellipse([600 + dw - 40, FLOOR - 200, 600 + dw - 22, FLOOR - 182], fill=GOLD, outline=INK)
        if who == "book":
            if u < 1.2:
                p = pose_from(lean=8, al=30, bl=-80, ar=40, br=-90)
                stick(c, p, x0 + 120, FLOOR, "calm", 1, who="book")
                book(d, *at(p, "hl", x0 + 120, FLOOR))
                bubble_at(c, "HOW TO OPEN A LOCK", 150, 250, prog(u, 0.15, 0.2))
            else:
                k = math.sin(u * 30) * 6 * (u < 1.9)
                p = pose_from(lean=20, ar=80, br=-20, al=70, bl=-10)
                stick(c, p, 520 + k, FLOOR, "o" if u > 1.6 else "calm", 1, who="book")
                if u > 1.75:
                    bubble_at(c, "?!", 380, 300, prog(u, 1.75, 0.2))
        else:
            if u < 1.0:
                p = walk(u * 9)
                x = x0 + (480 - x0) * out_cubic(u)
                stick(c, p, x, FLOOR, "calm", 1, who="rich")
                cash(d, *at(p, "hr", x, FLOOR))
                bubble_at(c, "OPEN.", x - 80, 280, prog(u, 0.45, 0.2))
            else:
                x = 480 + (900 - 480) * clamp((u - 1.25) / 0.9)
                stick(c, walk(u * 9), x, FLOOR, "happy", 1, who="rich")
    elif i == 1:   # RIVER
        if who == "book":
            if u < 0.9:
                p = pose_from(lean=6, al=30, bl=-80)
                stick(c, p, 300, FLOOR, "calm", 1, who="book")
                book(d, *at(p, "hl", 300, FLOOR), (60, 110, 190))
                bubble_at(c, "SWIMMING 101", 140, 250, prog(u, 0.1, 0.2))
            else:
                w = (u - 0.9)
                y = FLOOR + 60 + math.sin(w * 14) * 14
                p = pose_from(lean=0, al=-150 + math.sin(w * 20) * 30, bl=-20, ar=150 - math.sin(w * 20) * 30, br=20)
                stick(c, p, 600, y, "o", 1, who="book")
                d.rectangle([430, FLOOR + 40, 1010, LANE_H], fill=(70, 140, 210))   # water in front of him
                for k in range(3):
                    r_ = 30 + ((w * 60 + k * 25) % 70)
                    d.ellipse([600 - r_, FLOOR + 30 - r_ * 0.2, 600 + r_, FLOOR + 30 + r_ * 0.2], outline=(220, 240, 255), width=4)
                bubble_at(c, "HELP!", 470, 340, prog(u, 1.3, 0.2))
        else:
            bx = 1200 - 700 * out_cubic(clamp((u - 0.3) / 0.7))
            if u > 1.3:
                bx = 500 + 600 * clamp((u - 1.4) / 0.9)
            # yacht
            d.polygon([(bx - 170, FLOOR - 20), (bx + 190, FLOOR - 20), (bx + 140, FLOOR + 50), (bx - 130, FLOOR + 50)], fill=(250, 250, 250), outline=INK)
            d.rectangle([bx - 80, FLOOR - 90, bx + 90, FLOOR - 20], fill=(230, 232, 236), outline=INK, width=5)
            d.rectangle([bx - 60, FLOOR - 76, bx + 70, FLOOR - 50], fill=(70, 120, 170))
            if u < 1.3:
                p = pose_from(lean=0, ar=60, br=-60)
                stick(c, p, 330, FLOOR, "calm", 1, who="rich")
                cash(d, *at(p, "hr", 330, FLOOR))
                bubble_at(c, "BOAT.", 230, 300, prog(u, 0.2, 0.2))
            else:
                stick(c, pose_from(lean=-4, al=-150, ar=150), bx - 30, FLOOR - 90, "happy", 1, who="rich")
    elif i == 2:   # WALL
        if who == "book":
            d.rectangle([110, FLOOR - 330, 330, FLOOR - 170], fill=(40, 60, 50), outline=INK, width=6)
            for k in range(4):
                d.line([(130, FLOOR - 300 + k * 32), (130 + 40 + (k * 53) % 140, FLOOR - 300 + k * 32)], fill=(230, 230, 220), width=4)
            if u < 1.1:
                stick(c, pose_from(lean=0, ar=70, br=-80), 400, FLOOR, "calm", -1, who="book")
            else:
                j = clamp((u - 1.1) / 0.45)
                y = FLOOR - math.sin(j * math.pi) * 120
                stick(c, pose_from(lean=10, al=150, ar=160), 530, y, "o" if j > 0.5 else "calm", 1, who="book")
                if u > 1.6:
                    bubble_at(c, "BONK.", 390, 300, prog(u, 1.6, 0.2))
        else:
            ly = -200 + 520 * out_cubic(clamp((u - 0.3) / 0.6))
            # helicopter (only its belly shows) and a rope ladder
            d.ellipse([360, ly - 140, 700, ly - 20], fill=(60, 64, 72), outline=INK, width=6)
            d.line([(300, ly - 150), (760, ly - 150)], fill=INK, width=8)
            for side in (500, 560):
                d.line([(side, ly - 30), (side, ly + 380)], fill=(120, 90, 60), width=5)
            for k in range(8):
                d.line([(500, ly + k * 48), (560, ly + k * 48)], fill=(120, 90, 60), width=5)
            if u < 1.3:
                p = pose_from(lean=0, ar=60, br=-60)
                stick(c, p, 330, FLOOR, "calm", 1, who="rich")
                cash(d, *at(p, "hr", 330, FLOOR))
                bubble_at(c, "UP.", 240, 300, prog(u, 0.2, 0.2))
            else:
                up = out_cubic(clamp((u - 1.35) / 0.9))
                stick(c, pose_from(lean=0, al=-170, ar=170), 530, FLOOR - 80 - up * 600, "happy", 1, who="rich")
    else:          # JOB INTERVIEW
        desk(d)
        boss_stands = who == "rich" and u > 0.9
        bp = pose_from(lean=0, dy=0 if boss_stands else 0, al=-12, ar=12)
        stick(c, bp, 760, FLOOR - 120 if not boss_stands else FLOOR - 160, "happy" if boss_stands else "calm", -1, S * 0.9, body=(170, 170, 170))
        desk(d)
        if who == "book":
            p = pose_from(lean=6, ar=70, br=-40)
            stick(c, p, 420, FLOOR, "sad" if u > 1.3 else "calm", 1, who="book")
            hx, hy = at(p, "hr", 420, FLOOR)
            d.rectangle([hx - 26, hy - 34, hx + 26, hy + 30], fill=(250, 246, 232), outline=INK, width=3)
            d.ellipse([hx - 8, hy + 6, hx + 8, hy + 22], fill=(200, 60, 60))
            bubble_at(c, "WE'LL CALL YOU.", 560, 220, prog(u, 0.9, 0.2))
        else:
            x = 120 + (420 - 120) * out_cubic(clamp(u / 0.8))
            stick(c, walk(u * 9) if u < 0.8 else pose_from(lean=0), x, FLOOR, "happy", 1, who="rich")
            bubble_at(c, "WELCOME, SIR.", 560, 220, prog(u, 0.95, 0.2))
    return c


# ---------------------------------------------------------------- the twist (full screen)
def twist(t):
    u = (t - T_TWIST) * TS2
    yy = np.linspace(0, 1, H)[:, None, None]
    c = Image.fromarray(np.repeat((np.array([232, 230, 226], np.float32) * (1 - yy) + np.array([200, 196, 190], np.float32) * yy), W, axis=1).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(c)
    fl = 1500
    d.rectangle([0, fl, W, H], fill=(140, 110, 86))
    d.rectangle([600, 300, 960, 700], fill=(170, 210, 240), outline=(120, 124, 130), width=10)   # window
    d.rounded_rectangle([380, 230, 700, 300], 10, fill=(60, 50, 44), outline=INK, width=5)       # name plate on the wall
    d.text((540, 266), "CEO", font=FM(46), fill=GOLD, anchor="mm")
    # the boss behind his desk, chair turned away until u = 1.1
    turn = clamp((u - 1.1) / 0.35)
    bx = 700
    if turn >= 0.5:
        p = pose_from(lean=0, al=-20, bl=60, ar=20, br=-60)
        stick(c, p, bx, fl - 150, "happy", -1, 1.0, who="rich")
    chair_w = 300 * abs(1 - 2 * turn) if turn < 1 else 0
    if turn < 1:
        d.rounded_rectangle([bx - chair_w / 2, fl - 640, bx + chair_w / 2, fl - 250], 40, fill=(40, 34, 32), outline=INK, width=8)
    d.rectangle([440, fl - 270, 980, fl - 230], fill=(120, 86, 60), outline=INK, width=6)
    d.rectangle([470, fl - 230, 950, fl], fill=(104, 74, 52), outline=INK, width=6)
    # the book-smart one walks in with his diploma
    x = -100 + 380 * out_cubic(clamp(u / 0.9))
    walk = pose_from(lean=8, tl=25 * math.sin(u * 10), sl=-30, tr=-25 * math.sin(u * 10), sr=-30, ar=60, br=-50)
    p = walk if u < 0.9 else pose_from(lean=0 if turn < 1 else -8, ar=60, br=-50, al=-20 if turn < 1 else -60, bl=10)
    stick(c, p, x, fl, "o" if turn >= 1 else "happy", 1, 1.0, who="book")
    hx, hy = at(p, "hr", x, fl, 1.0)
    d.rectangle([hx - 30, hy - 40, hx + 30, hy + 36], fill=(250, 246, 232), outline=INK, width=4)
    d.ellipse([hx - 10, hy + 6, hx + 10, hy + 26], fill=(200, 60, 60))
    if 0.3 < u < 1.2:
        bubble_at(c, "HI! I GOT THE JOB.", 120, 820, prog(u, 0.3, 0.2), 1 - prog(u, 1.05, 0.15))
    if u > 1.5:
        bubble_at(c, "YOU'RE HIRED.", 560, 860, prog(u, 1.5, 0.2))
    if u > 2.2:
        bubble_at(c, "...", 120, 900, prog(u, 2.2, 0.2))
    return c


# ---------------------------------------------------------------- frame
def score_badge(c, book_n, rich_n, title, pulse):
    pw, ph = 620, 120
    k = 2
    im = Image.new("RGBA", (pw * k, ph * k), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([0, 0, pw * k, ph * k], 60 * k, fill=(28, 26, 34, 245), outline=(255, 255, 255, 255), width=4 * k)
    im = im.resize((pw, ph), Image.LANCZOS)
    dd = ImageDraw.Draw(im)
    dd.text((pw / 2, 30), title, font=FM(26), fill=(200, 200, 200), anchor="mm")
    dd.text((150, 78), f"BOOKS {book_n}", font=FM(40), fill=(240, 240, 236), anchor="mm")
    dd.text((pw / 2, 78), ":", font=FM(40), fill=(150, 150, 150), anchor="mm")
    dd.text((pw - 150, 78), f"{rich_n} MONEY", font=FM(40), fill=GOLD, anchor="mm")
    put(c, im, W / 2, 960, pulse)


def frame_raw(t):
    if t >= T_TWIST:
        c = twist(t)
        if t >= T_TEXT:
            p = out_cubic(prog(t, T_TEXT, 0.4))
            c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(150 * p))))
            chars = int((t - T_TEXT - 0.3) / 0.05)
            l1 = LINE1[:max(0, chars)]
            l2 = LINE2[:max(0, chars - len(LINE1) - 4)]
            cur = "_" if int(t * 3) % 2 == 0 else " "
            if l1:
                im = mono_text(l1 + (cur if not l2 else ""), 46, (245, 245, 240), 1)
                c.alpha_composite(im, (int(W / 2 - mono_text(LINE1, 46, spacing=1).width / 2), 780))
            if l2:
                im = mono_text(l2 + cur, 46, GOLD, 1)
                c.alpha_composite(im, (int(W / 2 - mono_text(LINE2, 46, spacing=1).width / 2), 850))
        return c
    c = Image.new("RGBA", (W, H), (20, 20, 24, 255))
    i, u = vig_at(t)
    for who, y0 in LANES.items():
        cur = lane(i, who, u * TS)
        if i > 0 and u < SLIDE:          # the new obstacle slides in over the last one
            p = out_cubic(u / SLIDE)
            prev = lane(i - 1, who, (V - 0.01) * TS)
            c.alpha_composite(prev, (int(-W * p), y0))
            c.alpha_composite(cur, (int(W * (1 - p)), y0))
        else:
            c.alpha_composite(cur, (0, y0))
    # lane labels
    for who, y0, txt in (("book", 0, "BOOK SMART"), ("rich", 972 + 52, "RICH KID")):
        im = mono_text(txt, 34, (255, 255, 255), 6)
        bg = Image.new("RGBA", (im.width + 40, im.height + 14), (20, 20, 24, 200))
        bg.alpha_composite(im, (20, 7))
        put(c, bg, W / 2, y0 + 60)
    rich_n = sum(1 for k in range(4) if t >= k * V + 1.2 / TS)
    title = OBST[i]
    pulse = 1 + 0.12 * math.exp(-((u - 1.2 / TS) * 8) ** 2)
    score_badge(c, 0, rich_n, title, pulse)
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
    for b in range(11):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        twist_bar = t0 >= T_TWIST - 0.01
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), BAR + 0.05, (1, 0.4, 0.15, 0.05), a=0.02, d=1.2), t0, 0.05, (k - 1.5) * 0.35)
        for q in range(4):
            tb = t0 + q * beat
            mix_in(mus, tone(110, 0.3, (1,), a=0.002, d=0.1, sweep=42), tb, 0.6 if q % 2 == 0 else 0.4)
            mix_in(mus, tone(midi(rt), beat * 0.45, (1, 0.5, 0.15), a=0.004, d=0.12), tb, 0.25)
            mix_in(mus, tone(midi(rt), beat * 0.45, (1, 0.5, 0.15), a=0.004, d=0.12), tb + beat / 2, 0.18)
            if q % 2 == 1:
                mix_in(mus, tone(330, 0.16, (1, 0.6, 0.45, 0.3, 0.2), a=0.002, d=0.04, sweep=190), tb, 0.13)
            for e in range(2):
                mix_in(mus, tone(3000, 0.03, (1,), a=0.0008, d=0.006), tb + e * beat / 2, 0.035, 0.4 - 0.8 * e)
            if not twist_bar:   # a cheeky plucked line
                m = ch[(q + b) % 4] + 12
                mix_in(mus, tone(midi(m), 0.3, (1, 0.3, 0.1), a=0.003, d=0.1), tb + beat * 0.75, 0.07, 0.2)
    for i in range(4):
        t0 = i * V
        if i:   # whoosh on each new obstacle
            ts = np.arange(int(0.3 * SR)) / SR
            fr = 400 * (1400 / 400) ** (ts / 0.3)
            wh = sum(np.sin(2 * np.pi * np.cumsum(fr * m) / SR) / (q + 1) for q, m in enumerate([1, 1.01, 1.5])) * np.sin(np.pi * ts / 0.3) ** 2
            mix_in(fx, wh, t0 - 0.05, 0.06)
        # the book one fails: a low bonk sliding down
        mix_in(fx, tone(220, 0.35, (1, 0.5), a=0.002, d=0.12, sweep=90), t0 + 1.7 / TS, 0.18, -0.3)
        # the rich one wins: cha-ching (two bright bells)
        for k, m in enumerate([88, 93]):
            mix_in(fx, tone(midi(m), 0.6, (1, 0.4, 0.2), a=0.001, d=0.18), t0 + 1.2 / TS + k * 0.08, 0.09, 0.3)
        for k in range(4):   # a few coins
            mix_in(fx, tone(2600 + 300 * k, 0.08, (1,), a=0.0008, d=0.02), t0 + 1.25 / TS + k * 0.05, 0.04, 0.4)
    # the twist: the chair turns - dun dun
    for k, (m, d_) in enumerate([(38, 0.5), (37, 1.1)]):
        mix_in(fx, tone(midi(m), d_ + 0.4, (1, 0.6, 0.4, 0.25), a=0.005, d=0.5), T_TWIST + 1.1 / TS2 + k * 0.35, 0.3)
    mix_in(fx, tone(80, 0.9, (1, 0.5), a=0.002, d=0.3, sweep=32), T_TWIST + 1.1 / TS2, 0.6)
    total = len(LINE1) + 4 + len(LINE2)
    for i in range(total):
        ch_ = (LINE1 + "    " + LINE2)[i]
        if ch_ != " ":
            mix_in(fx, tone(1700 + (i % 3) * 140, 0.025, (1, 0.4), a=0.0006, d=0.005), T_TEXT + 0.3 + i * 0.05, 0.05)
    x = mus + fx
    x -= x.mean(axis=0)
    x = np.tanh(x * 1.3)
    x *= 0.89 / np.abs(x).max()
    r = int(0.005 * SR)
    x[:r] *= np.linspace(0, 1, r)[:, None]
    x[-r:] *= np.linspace(1, 0, r)[:, None]
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "out/books-vs-money.mp4"
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
