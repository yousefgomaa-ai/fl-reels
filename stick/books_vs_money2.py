#!/usr/bin/env python3
"""BOOK SMART vs RICH KID, with the twist kept for the end (owner, 2026-11-19).

Four obstacles: the book-smart one solves each one cleverly (picks the lock, builds a raft, builds a ladder, aces the
exam) while the rich kid lounges with a juice and does nothing - BOOKS 4 : 0 MONEY. At the finish line the rich kid is
already on the podium. "HOW?!" - "I PAID." A "MEANWHILE..." flashback shows him carried past every obstacle, the
score turns 4 : 4, and the line is typed: "SMART PEOPLE SOLVE PROBLEMS. / RICH PEOPLE PAY THEM TO."
28.8 s (12 bars at 100 bpm), loops on itself.

    python3 stick/books_vs_money2.py out/books-vs-money-2.mp4
    ONLY_FRAMES=2,6,10,14,16.5,19,22,25 python3 stick/books_vs_money2.py out/b2.mp4
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scroller_reader import GOLD, INK, clamp, midi, mix_in, out_back, out_cubic, prog, put, tone, write_wav  # noqa
from keep_trying import pose_from  # noqa
from motivation_bus import FM, mono_text  # noqa
import books_vs_money as B  # noqa  (sets, stickman helpers, the rich kid's "paid" versions of the obstacles)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BAR = 4 * 60 / BPM
DUR = 12 * BAR                     # 28.8 s
V = 3.8
TS = 2.5 / V                       # moves are timed in 2.5 s units, played over V
T_FIN = 4 * V                      # 15.2: the finish line
F_HOW, F_PAID, F_FLASH, F_FLASH_END = T_FIN + 1.3, T_FIN + 2.1, T_FIN + 2.9, T_FIN + 6.2
T_TEXT = T_FIN + 6.4
T_LOOP = DUR - 0.45
OBST = ["LOCKED DOOR", "RIVER", "WALL", "FINAL EXAM"]
SOLVED = [1.6, 1.9, 1.8, 1.4]      # when the book-smart one clears each obstacle (in 2.5 s units)
LOUNGE = ["LATER.", "ZZZ...", "BORING.", "ZZZ..."]
LINE1, LINE2 = "SMART PEOPLE SOLVE PROBLEMS.", "RICH PEOPLE PAY THEM TO."
FLOOR, S = B.FLOOR, B.S


def books_at(t):
    return sum(1 for k in range(4) if t >= k * V + SOLVED[k] / TS)


# ---------------------------------------------------------------- the exam set (classroom)
def exam_bg():
    im = B.sky((236, 232, 220), (214, 208, 194))
    d = ImageDraw.Draw(im)
    d.rectangle([90, 120, 520, 360], fill=(46, 70, 58), outline=(120, 90, 60), width=10)
    for k in range(4):
        d.line([(120, 160 + k * 46), (140 + 60 + (k * 77) % 280, 160 + k * 46)], fill=(230, 230, 220), width=4)
    d.rectangle([0, FLOOR, W, B.LANE_H], fill=(150, 120, 96))
    return im


def school_desk(d, x):
    d.rectangle([x - 120, FLOOR - 150, x + 120, FLOOR - 128], fill=(150, 110, 70), outline=INK, width=5)
    for lx in (x - 105, x + 95):
        d.rectangle([lx, FLOOR - 128, lx + 12, FLOOR], fill=(90, 90, 96), outline=INK, width=2)


def paper(d, x, y, grade=None):
    d.rectangle([x - 34, y - 22, x + 34, y + 22], fill=(252, 250, 244), outline=INK, width=3)
    if grade:
        d.text((x, y), grade, font=FM(30), fill=(210, 40, 40), anchor="mm")
    else:
        for k in range(3):
            d.line([(x - 24, y - 10 + k * 10), (x + 20, y - 10 + k * 10)], fill=(150, 150, 160), width=2)


# ---------------------------------------------------------------- the book-smart lane: he solves it
def book_lane(i, u):
    c = (exam_bg() if i == 3 else B.set_bg(i)).copy()
    d = ImageDraw.Draw(c)
    walk = lambda ph: pose_from(lean=10, tl=30 * math.sin(ph), sl=-30, tr=-30 * math.sin(ph), sr=-30,
                                al=-25 * math.sin(ph), bl=40, ar=25 * math.sin(ph), br=40)
    reading = pose_from(lean=8, al=30, bl=-80, ar=40, br=-90)
    if i == 0:   # picks the lock
        opened = clamp((u - 1.6) / 0.3)
        dw = 190 * (1 - opened * 0.82)
        d.rectangle([600, FLOOR - 380, 800, FLOOR], fill=(40, 30, 26))
        d.rectangle([600, FLOOR - 380, 600 + dw, FLOOR], fill=(110, 72, 46), outline=INK, width=6)
        if dw > 60:
            d.ellipse([600 + dw - 40, FLOOR - 200, 600 + dw - 22, FLOOR - 182], fill=GOLD, outline=INK)
        if u < 0.8:
            B.stick(c, reading, 300, FLOOR, "calm", 1, who="book")
            B.book(d, *B.at(reading, "hl", 300, FLOOR))
            B.bubble_at(c, "HOW TO PICK A LOCK", 150, 250, prog(u, 0.1, 0.2))
        elif u < 1.2:
            x = 300 + 260 * (u - 0.8) / 0.4
            B.stick(c, walk(u * 12), x, FLOOR, "calm", 1, who="book")
        elif u < 1.7:
            p = pose_from(lean=25, dy=20, ar=70, br=-10, al=60, bl=-20)
            B.stick(c, p, 560, FLOOR, "calm", 1, who="book")
            for k in range(3):   # little sparks at the lock
                a = u * 20 + k * 2
                d.line([(760 + 18 * math.cos(a), FLOOR - 191 + 18 * math.sin(a)), (760 + 30 * math.cos(a), FLOOR - 191 + 30 * math.sin(a))], fill=GOLD, width=4)
            B.bubble_at(c, "CLICK.", 520, 300, prog(u, 1.5, 0.15))
        else:
            x = 560 + 420 * clamp((u - 1.75) / 0.7)
            B.stick(c, walk(u * 12), x, FLOOR, "happy", 1, who="book")
    elif i == 1:  # builds a raft
        if u < 0.7:
            B.stick(c, reading, 300, FLOOR, "calm", 1, who="book")
            B.book(d, *B.at(reading, "hl", 300, FLOOR), (60, 110, 190))
            B.bubble_at(c, "HOW TO BUILD A RAFT", 120, 250, prog(u, 0.1, 0.2))
        else:
            built = out_back(clamp((u - 0.7) / 0.3), 2)
            rx = 470 + 470 * clamp((u - 1.05) / 0.85)
            for k in range(4):   # logs
                y = FLOOR + 6 + (k - 1.5) * 4
                d.rounded_rectangle([rx - 110 * built, y - 14, rx + 110 * built, y + 14], 12, fill=(150, 104, 64), outline=INK, width=4)
            if built > 0.9:
                p = pose_from(lean=6, al=60, bl=-30, ar=50, br=-20)
                B.stick(c, p, rx, FLOOR - 14, "happy" if u > 1.9 else "calm", 1, who="book")
                hx, hy = B.at(p, "hr", rx, FLOOR - 14)
                d.line([(hx, hy - 60), (hx + 30, hy + 90)], fill=(120, 84, 50), width=8)   # paddle
            else:
                B.stick(c, pose_from(lean=0), 330, FLOOR, "calm", 1, who="book")
    elif i == 2:  # builds a ladder
        d.rectangle([110, FLOOR - 330, 330, FLOOR - 170], fill=(40, 60, 50), outline=INK, width=6)
        d.text((220, FLOOR - 250), "75°", font=FM(48), fill=(235, 235, 225), anchor="mm")
        lad = clamp((u - 0.6) / 0.3)
        if lad > 0:   # ladder leaning on the wall
            top = (600, 140 + (1 - lad) * 400)
            for dx in (0, 60):
                d.line([(440 + dx, FLOOR), (top[0] - 40 + dx, top[1])], fill=(150, 104, 64), width=10)
            for k in range(1, 9):
                f = k / 9
                y = FLOOR + (top[1] - FLOOR) * f
                x = 440 + (top[0] - 40 - 440) * f
                d.line([(x, y), (x + 60, y)], fill=(150, 104, 64), width=7)
        if u < 0.9:
            B.stick(c, pose_from(lean=0, ar=70, br=-80), 380, FLOOR, "calm", -1, who="book")
        else:
            f = clamp((u - 0.9) / 1.0)
            x = 470 + (600 - 470) * f
            y = FLOOR - (FLOOR - 140) * f
            cl = pose_from(lean=10, tl=40 * math.sin(u * 14), sl=-60, tr=-20, sr=-60, al=150, ar=130)
            B.stick(c, cl if f < 1 else pose_from(lean=-4, al=-150, ar=150), x, y, "happy" if f >= 1 else "calm", 1, who="book")
    else:         # aces the exam
        school_desk(d, 560)
        p = pose_from(lean=14, dy=60, tl=70, sl=-70, tr=60, sr=-60, ar=70 + math.sin(u * 30) * 12 * (u < 1.3), br=-40)
        B.stick(c, p, 470, FLOOR, "happy" if u > 1.35 else "calm", 1, who="book")
        paper(d, 600, FLOOR - 172, "A+" if u > 1.35 else None)
        if u > 1.35:
            B.bubble_at(c, "EASY.", 420, 300, prog(u, 1.4, 0.2))
    return c


# ---------------------------------------------------------------- the rich lane: he lounges
def lounge_chair(d, x):
    d.polygon([(x - 120, FLOOR - 70), (x + 110, FLOOR - 70), (x + 160, FLOOR - 220), (x + 120, FLOOR - 225), (x + 80, FLOOR - 100), (x - 120, FLOOR - 100)],
              fill=(240, 120, 90), outline=INK)
    for lx in (x - 100, x + 90):
        d.line([(lx, FLOOR - 70), (lx, FLOOR)], fill=INK, width=8)


def rich_lane(i, u):
    c = (exam_bg() if i == 3 else B.set_bg(i)).copy()
    d = ImageDraw.Draw(c)
    if i == 0:
        d.rectangle([600, FLOOR - 380, 790, FLOOR], fill=(110, 72, 46), outline=INK, width=6)
        d.ellipse([750, FLOOR - 200, 768, FLOOR - 182], fill=GOLD, outline=INK)
    elif i == 2:
        pass
    elif i == 3:
        school_desk(d, 760)
        paper(d, 760, FLOOR - 172)
    x = 300
    lounge_chair(d, x)
    sip = math.sin(u * 2.4)
    p = pose_from(lean=-35, dy=95, tl=88, sl=-20, tr=80, sr=-10, al=10, bl=-150 + sip * 10, ar=60, br=60)
    B.stick(c, p, x + 30, FLOOR - 10, "happy", 1, who="rich")
    hx, hy = B.at(p, "hl", x + 30, FLOOR - 10)
    d.rounded_rectangle([hx - 12, hy - 34, hx + 14, hy + 6], 5, fill=(255, 170, 60), outline=INK, width=3)   # juice
    d.line([(hx + 4, hy - 34), (hx + 14, hy - 56)], fill=(240, 80, 120), width=4)
    B.bubble_at(c, LOUNGE[i], 280, 360, prog(u, 0.6, 0.2))
    return c


# ---------------------------------------------------------------- the rich kid getting through (flashback panels)
def paid_panel(i, u):
    if i < 3:
        return B.lane(i, "rich", u)      # doorman/cash, yacht, helicopter - from the first version
    c = exam_bg().copy()                 # a tutor writes his exam while he sips
    d = ImageDraw.Draw(c)
    school_desk(d, 560)
    tp = pose_from(lean=14, dy=60, tl=70, sl=-70, tr=60, sr=-60, ar=70 + math.sin(u * 30) * 12, br=-40)
    B.stick(c, tp, 470, FLOOR, "calm", 1, body=(170, 170, 170))
    paper(d, 600, FLOOR - 172, "A+" if u > 1.2 else None)
    p = pose_from(lean=-4, al=10, bl=-150, ar=12)
    B.stick(c, p, 820, FLOOR, "happy", -1, who="rich")
    B.cash(d, 700, FLOOR - 250)
    return c


# ---------------------------------------------------------------- finish line (full screen)
def finish(t):
    u = t - T_FIN
    yy = np.linspace(0, 1, H)[:, None, None]
    c = Image.fromarray(np.repeat(np.array([150, 200, 240], np.float32) * (1 - yy) + np.array([220, 236, 246], np.float32) * yy, W, axis=1).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(c)
    fl = 1450
    d.rectangle([0, fl, W, H], fill=(116, 170, 96))
    # finish banner
    d.line([(620, fl), (620, 400)], fill=INK, width=12)
    d.line([(1040, fl), (1040, 400)], fill=INK, width=12)
    d.rectangle([600, 340, 1060, 440], fill=(250, 250, 250), outline=INK, width=6)
    for k in range(9):
        for r_ in range(2):
            if (k + r_) % 2 == 0:
                d.rectangle([600 + k * 51, 340 + r_ * 50, 651 + k * 51, 390 + r_ * 50], fill=INK)
    d.text((830, 490), "FINISH", font=FM(54), fill=INK, anchor="mm")
    # podium with the rich kid already on it
    d.rectangle([700, fl - 200, 960, fl], fill=(250, 210, 90), outline=INK, width=6)
    d.text((830, fl - 100), "1", font=FM(110), fill=INK, anchor="mm")
    rp = pose_from(lean=-2, al=-160, bl=-10, ar=10, br=-140)
    B.stick(c, rp, 830, fl - 200, "happy", -1, 1.0, who="rich")
    hx, hy = B.at(rp, "hl", 830, fl - 200, 1.0)
    d.polygon([(hx - 40, hy - 70), (hx + 40, hy - 70), (hx + 26, hy - 10), (hx - 26, hy - 10)], fill=GOLD, outline=INK)   # trophy
    d.rectangle([hx - 10, hy - 10, hx + 10, hy + 14], fill=GOLD, outline=INK)
    jx, jy = B.at(rp, "hr", 830, fl - 200, 1.0)
    d.rounded_rectangle([jx - 14, jy - 40, jx + 16, jy + 6], 5, fill=(255, 170, 60), outline=INK, width=3)
    # the book-smart one runs in, arms up... then stops
    run_in = clamp(u / 1.1)
    x = -120 + 480 * out_cubic(run_in)
    if u < 1.1:
        bp = pose_from(lean=12, tl=40 * math.sin(u * 12), sl=-40, tr=-40 * math.sin(u * 12), sr=-40, al=-150, ar=150)
        face = "happy"
    else:
        bp = pose_from(lean=-6, al=-30, bl=60, ar=30, br=-60)
        face = "o"
    B.stick(c, bp, x, fl, face, 1, 1.0, who="book")
    if u > 1.3:
        B.bubble_at(c, "HOW?!", 180, 820, prog(u, 1.3, 0.2), 1 - prog(u, 2.75, 0.15))
    if u > 2.1:
        B.bubble_at(c, "I PAID.", 640, 920, prog(u, 2.1, 0.2), 1 - prog(u, 2.75, 0.15))
    # MEANWHILE... the four ways he was carried through
    if F_FLASH <= t < F_FLASH_END + 0.3:
        a = out_cubic(prog(t, F_FLASH, 0.3)) * (1 - prog(t, F_FLASH_END, 0.3))
        c.alpha_composite(Image.new("RGBA", (W, H), (16, 16, 20, int(220 * a))))
        put(c, mono_text("MEANWHILE...", 54, (255, 255, 255), 4), W / 2, 330, 1, a)
        fu = (t - F_FLASH) * 2.5 / (F_FLASH_END - F_FLASH)
        for k in range(4):
            pnl = paid_panel(k, clamp(fu, 0, 2.49)).resize((500, 439), Image.LANCZOS)
            fr = Image.new("RGBA", (512, 451), (255, 255, 255, 255))
            fr.alpha_composite(pnl, (6, 6))
            put(c, fr, 280 + (k % 2) * 520, 660 + (k // 2) * 470, 0.9 + 0.1 * out_back(prog(t, F_FLASH + k * 0.15, 0.3)), a)
    return c


# ---------------------------------------------------------------- score
def score_badge(c, b_n, r_n, title, pulse=1.0, y=960):
    pw, ph = 640, 120
    k = 2
    im = Image.new("RGBA", (pw * k, ph * k), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, pw * k, ph * k], 60 * k, fill=(28, 26, 34, 245), outline=(255, 255, 255, 255), width=4 * k)
    im = im.resize((pw, ph), Image.LANCZOS)
    dd = ImageDraw.Draw(im)
    dd.text((pw / 2, 30), title, font=FM(26), fill=(200, 200, 200), anchor="mm")
    dd.text((160, 78), f"BOOKS {b_n}", font=FM(40), fill=(240, 240, 236), anchor="mm")
    dd.text((pw / 2, 78), ":", font=FM(40), fill=(150, 150, 150), anchor="mm")
    dd.text((pw - 160, 78), f"{r_n} MONEY", font=FM(40), fill=GOLD, anchor="mm")
    put(c, im, W / 2, y, pulse)


def money_at(t):
    if t < F_FLASH + 0.4:
        return 0
    return min(4, 1 + int((t - F_FLASH - 0.4) / 0.6))


def frame_raw(t):
    if t >= T_FIN:
        c = finish(t)
        if t >= F_FLASH:
            m = money_at(t)
            pulse = 1 + 0.15 * math.exp(-(((t - F_FLASH - 0.4) % 0.6) * 9) ** 2) if m < 4 or t < F_FLASH + 2.4 else 1
            score_badge(c, 4, m, "FINAL SCORE", pulse, 1640 if t < T_TEXT else 1300)
        else:
            score_badge(c, 4, 0, "FINAL SCORE", 1, 1640)
        if t >= T_TEXT:
            p = out_cubic(prog(t, T_TEXT, 0.4))
            c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(160 * p))))
            score_badge(c, 4, 4, "FINAL SCORE", 1, 1300)
            chars = int((t - T_TEXT - 0.3) / 0.05)
            l1 = LINE1[:max(0, chars)]
            l2 = LINE2[:max(0, chars - len(LINE1) - 4)]
            cur = "_" if int(t * 3) % 2 == 0 else " "
            if l1:
                im = mono_text(l1 + (cur if not l2 else ""), 44, (245, 245, 240), 1)
                c.alpha_composite(im, (int(W / 2 - mono_text(LINE1, 44, spacing=1).width / 2), 760))
            if l2:
                im = mono_text(l2 + cur, 44, GOLD, 1)
                c.alpha_composite(im, (int(W / 2 - mono_text(LINE2, 44, spacing=1).width / 2), 830))
        return c
    c = Image.new("RGBA", (W, H), (20, 20, 24, 255))
    i = min(3, int(t // V))
    u = t - i * V
    for who, y0, fn in (("book", 0, book_lane), ("rich", 972, rich_lane)):
        cur = fn(i, u * TS)
        if i > 0 and u < B.SLIDE:
            p = out_cubic(u / B.SLIDE)
            c.alpha_composite(fn(i - 1, (V - 0.01) * TS), (int(-W * p), y0))
            c.alpha_composite(cur, (int(W * (1 - p)), y0))
        else:
            c.alpha_composite(cur, (0, y0))
    for y0, txt in ((0, "BOOK SMART"), (972 + 52, "RICH KID")):
        im = mono_text(txt, 34, (255, 255, 255), 6)
        bg = Image.new("RGBA", (im.width + 40, im.height + 14), (20, 20, 24, 200))
        bg.alpha_composite(im, (20, 7))
        put(c, bg, W / 2, y0 + 60)
    pulse = 1 + 0.12 * math.exp(-((u - SOLVED[i] / TS) * 8) ** 2)
    score_badge(c, books_at(t), 0, OBST[i], pulse)
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
    chords = [[48, 55, 60, 64], [45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59]]
    roots = [36, 33, 29, 31]
    for b in range(12):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        reveal = t0 >= F_FLASH - 0.01
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m - (1 if reveal and k == 1 else 0)), BAR + 0.05, (1, 0.4, 0.15, 0.05), a=0.02, d=1.2), t0, 0.05, (k - 1.5) * 0.35)
        for q in range(4):
            tb = t0 + q * beat
            mix_in(mus, tone(110, 0.3, (1,), a=0.002, d=0.1, sweep=42), tb, 0.6 if q % 2 == 0 else 0.4)
            mix_in(mus, tone(midi(rt), beat * 0.45, (1, 0.5, 0.15), a=0.004, d=0.12), tb, 0.25)
            if q % 2 == 1:
                mix_in(mus, tone(330, 0.16, (1, 0.6, 0.45, 0.3, 0.2), a=0.002, d=0.04, sweep=190), tb, 0.13)
            for e in range(2):
                mix_in(mus, tone(3000, 0.03, (1,), a=0.0008, d=0.006), tb + e * beat / 2, 0.035, 0.4 - 0.8 * e)
            m = ch[(q + b) % 4] + 12
            mix_in(mus, tone(midi(m), 0.3, (1, 0.3, 0.1), a=0.003, d=0.1), tb + beat * 0.75, 0.06, 0.2)
    for i in range(4):
        t0 = i * V
        if i:
            ts = np.arange(int(0.3 * SR)) / SR
            fr = 400 * (1400 / 400) ** (ts / 0.3)
            wh = sum(np.sin(2 * np.pi * np.cumsum(fr * m) / SR) / (q + 1) for q, m in enumerate([1, 1.01, 1.5])) * np.sin(np.pi * ts / 0.3) ** 2
            mix_in(fx, wh, t0 - 0.05, 0.06)
        for k, m in enumerate([76, 79, 84]):     # the book-smart one scores: a bright little arpeggio
            mix_in(fx, tone(midi(m), 0.4, (1, 0.3), a=0.002, d=0.15), t0 + SOLVED[i] / TS + k * 0.07, 0.1, -0.3)
        mix_in(fx, tone(midi(67), 0.5, (1, 0.5, 0.2), a=0.01, d=0.2), t0 + 0.6 / TS, 0.05, 0.4)   # a lazy slurp below
    # finish line: a fanfare that turns sour on "HOW?!"
    for k, m in enumerate([60, 64, 67, 72]):
        mix_in(fx, tone(midi(m), 0.5, (1, 0.5, 0.3, 0.15), a=0.01, d=0.25), T_FIN + 0.1 + k * 0.12, 0.1)
    for k, (m, d_) in enumerate([(38, 0.5), (37, 1.0)]):
        mix_in(fx, tone(midi(m), d_ + 0.4, (1, 0.6, 0.4, 0.25), a=0.005, d=0.5), F_HOW + k * 0.35, 0.3)
    mix_in(fx, tone(80, 0.9, (1, 0.5), a=0.002, d=0.3, sweep=32), F_HOW, 0.6)
    # each obstacle he was carried past: cha-ching
    for k in range(4):
        tk = F_FLASH + 0.4 + k * 0.6
        for j, m in enumerate([88, 93]):
            mix_in(fx, tone(midi(m), 0.6, (1, 0.4, 0.2), a=0.001, d=0.18), tk + j * 0.08, 0.1, 0.3)
    total = len(LINE1) + 4 + len(LINE2)
    for i in range(total):
        if (LINE1 + "    " + LINE2)[i] != " ":
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
    out = sys.argv[1] if len(sys.argv) > 1 else "out/books-vs-money-2.mp4"
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
