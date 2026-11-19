#!/usr/bin/env python3
"""IDEAS.md #6 - EATS IT HOT vs PHOTOGRAPHS IT FIRST. Split screen, 18 s, loops on itself.

13:00, the same table, the same steaming bowl: "LUNCH!" Above, he just eats: the bowl empties, "FOOD TEMP 68°C",
EATEN HOT. Below, the phone comes out: a shot, another, he stands for the top view, crouches for "ONE MORE ANGLE",
adds a filter, posts - PHOTOS 1...47, the steam fades, FOOD TEMP falls 68 -> 19°C. 13:12, the first bite: "...COLD."
The post: 3 LIKES.  "HIS PHONE ATE FIRST. / HE GOT IT COLD."  FOLLOW FOR MORE.

    python3 stick/cold_food.py stick/cold-food.mp4
    ONLY_FRAMES=0.6,3.0,5.5,8.5,10.6,12.4,13.6,15.8 python3 stick/cold_food.py /tmp/cf
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
HOT_C, HOT_FAR = AJ.DOER, AJ.DOER_FAR
PIC_C, PIC_FAR = AJ.OT, AJ.OT_FAR
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP

SEAT_Y = FYP - 140
HIP = (250, SEAT_Y)
TABLE = (360, 740, FYP - 205)          # x0, x1, top y
PLATE_X = 470

# ---------------------------------------------------------------- timeline
T_EAT0, T_EAT1 = 1.6, 7.6
SHOTS = [1.9, 2.4, 2.9, 3.5, 4.0, 4.9, 5.3, 5.7, 6.1, 6.5, 7.0, 8.0, 8.4, 8.8, 9.2, 9.6]
T_STAND0, T_STAND1 = 4.5, 7.4
T_CROUCH0, T_CROUCH1 = 7.7, 9.9
T_EDIT0, T_POST = 10.0, 11.0
T_BITE = 11.9
T_LIKES = 13.1
T_CLOCK0, T_CLOCK1 = 1.6, 12.0
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "HIS PHONE ATE FIRST.", "HE GOT IT COLD."
T_FOLLOW = 16.95

BUB_BOTH = [(0.3, 1.5, "LUNCH!", "me")]
BUB_HOT = [(8.2, 9.6, "SO GOOD.", "me"), (10.4, 11.7, "PERFECT.", "me")]
BUB_PIC = [(1.9, 2.9, "WAIT. PHOTO FIRST.", "me"), (5.0, 6.2, "TOP VIEW.", "me"), (8.0, 9.4, "ONE MORE ANGLE.", "me"),
           (10.1, 11.0, "FILTER...", "me"), (12.3, 13.6, "...COLD.", "me")]


def clock_minutes(t):
    return int(13 * 60 + 12 * prog(t, T_CLOCK0, T_CLOCK1))


def photos(t):
    n = sum(1 for s in SHOTS if t >= s)
    if n == 0:
        return 0
    return int(1 + (47 - 1) * (n - 1) / (len(SHOTS) - 1))


def temp_c(t):
    return 68 - 49 * smooth(prog(t, 1.6, 12.0)) ** 0.8


# ---------------------------------------------------------------- poses
SIT = dict(AJ.SIT_TYPE)
EAT_DOWN = dict(SIT, head=(22, -144), neck=(14, -102), el=(56, -70), hl=(104, -74), er=(40, -56), hr=(88, -52))
EAT_UP = dict(SIT, head=(18, -146), neck=(12, -104), el=(50, -78), hl=(36, -128), er=(40, -56), hr=(88, -52))
LEAN_BACK = dict(SIT, head=(-6, -148), neck=(-4, -106), el=(16, -66), hl=(40, -56), er=(10, -62), hr=(36, -50))
STRETCH = dict(SIT, head=(-4, -150), neck=(-2, -108), el=(-24, -150), hl=(-36, -200), er=(22, -150), hr=(34, -200))
SIT_SHOOT = dict(SIT, head=(14, -148), neck=(8, -106), el=(50, -110), hl=(86, -132), er=(46, -104), hr=(82, -126))
SIT_EDIT = OC.SIT_PHONE
SIT_BITE = dict(EAT_UP, head=(14, -150))
STAND_SHOOT = dict(PW.STAND, head=(20, -146), neck=(12, -106), el=(50, -110), hl=(104, -96), er=(46, -104),
                   hr=(100, -90))
CROUCH = {"head": (34, -96), "neck": (24, -60), "el": (54, -70), "hl": (90, -96), "er": (50, -64), "hr": (86, -90),
          "kl": (40, 20), "fl": (10, 70), "kr": (30, 26), "fr": (0, 72)}


def eater(t):
    if T_EAT0 <= t < T_EAT1:
        ph = (t - T_EAT0) / 0.75 % 1.0
        k = 0.5 - 0.5 * math.cos(2 * math.pi * ph)
        return lerp_pose(EAT_DOWN, EAT_UP, k), HIP, "fork"
    if t >= T_EAT1:
        base = lerp_pose(EAT_DOWN, LEAN_BACK, smooth(prog(t, T_EAT1, T_EAT1 + 0.5)))
        k = smooth(prog(t, 10.2, 10.7)) * (1 - smooth(prog(t, 11.8, 12.3)))
        return lerp_pose(base, STRETCH, k), HIP, None
    return SIT, HIP, "fork"


def shooter(t):
    """pose, hip, prop"""
    if t < 1.7:
        return SIT, HIP, None
    if t < T_STAND0:
        return lerp_pose(SIT, SIT_SHOOT, smooth(prog(t, 1.7, 1.95))), HIP, "phone"
    if t < T_STAND1:
        k = smooth(prog(t, T_STAND0, T_STAND0 + 0.45))
        hip = (lerp(HIP[0], 330, k), lerp(HIP[1], FYP - 140, k))
        pose = lerp_pose(SIT_SHOOT, STAND_SHOOT, k)
        if k >= 1:
            hip = (330, FYP - 141 + 2 * math.sin(t * 3))
        return pose, hip, "phone"
    if t < T_CROUCH1:
        k = smooth(prog(t, T_STAND1, T_CROUCH0))
        hip = (lerp(330, 300, k), lerp(FYP - 140, FYP - 72, k))
        return lerp_pose(STAND_SHOOT, CROUCH, k), hip, "phone"
    if t < T_BITE:
        k = smooth(prog(t, T_CROUCH1, T_EDIT0 + 0.3))
        hip = (lerp(300, HIP[0], k), lerp(FYP - 72, HIP[1], k))
        return lerp_pose(CROUCH, SIT_EDIT, k), hip, "phone"
    k = smooth(prog(t, T_BITE, T_BITE + 0.35))
    return lerp_pose(SIT_EDIT, SIT_BITE, k), HIP, "fork"


# ---------------------------------------------------------------- room
def build_room():
    yy = np.mgrid[0:PH, 0:W][0].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + 9
    img = np.where((yy > FYP)[..., None], img * 0.8 + 8, img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(46, 44, 44, 255), width=2)
    # window with daylight
    x0, y0, x1, y1 = 470, 70, 720, 280
    for i in range(y1 - y0):
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=PW.lerp_c((120, 170, 225), (190, 220, 240), i / (y1 - y0)) + (255,))
    d.ellipse([x0 + 30, y0 + 30, x0 + 76, y0 + 76], fill=(255, 236, 160, 255))
    d.rectangle([x0, y0, x1, y1], outline=ink, width=8)
    d.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=ink, width=6)
    # chair
    d.rectangle([150, SEAT_Y + 4, 300, SEAT_Y + 20], fill=(100, 76, 56, 255), outline=ink, width=3)
    d.rectangle([150, SEAT_Y - 170, 166, FYP], fill=(100, 76, 56, 255), outline=ink, width=3)
    d.rectangle([284, SEAT_Y + 20, 298, FYP], fill=(100, 76, 56, 255), outline=ink, width=3)
    return im


def table_front(d):
    ink = INK + (255,)
    tx0, tx1, ty = TABLE
    d.rectangle([tx0, ty, tx1, ty + 18], fill=(150, 110, 76, 255), outline=ink, width=4)
    for lx in (tx0 + 20, tx1 - 40):
        d.rectangle([lx, ty + 18, lx + 18, FYP], fill=(130, 96, 66, 255), outline=ink, width=3)


def bowl(im, d, t, level, hot):
    ink = INK + (255,)
    ty = TABLE[2]
    cx = PLATE_X
    # food heap
    if level > 0.02:
        h = 34 * level
        d.ellipse([cx - 56, ty - 34 - h, cx + 56, ty - 34 + h * 0.6], fill=(236, 186, 80, 255), outline=ink, width=3)
        for j in range(int(5 * level)):
            ax = cx - 36 + j * 18
            d.arc([ax - 12, ty - 40 - h * 0.6, ax + 12, ty - 22 - h * 0.6], 180, 360, fill=(200, 140, 50, 255), width=3)
        if level > 0.3:
            d.ellipse([cx + 10, ty - 50 - h * 0.5, cx + 26, ty - 36 - h * 0.5], fill=(230, 70, 60, 255), outline=ink)
            d.ellipse([cx - 30, ty - 44 - h * 0.5, cx - 16, ty - 32 - h * 0.5], fill=(90, 170, 80, 255), outline=ink)
    d.chord([cx - 70, ty - 70, cx + 70, ty + 2], 0, 180, fill=(236, 238, 244, 255), outline=ink, width=4)
    d.line([(cx - 70, ty - 34), (cx + 70, ty - 34)], fill=ink, width=4)
    # steam
    if hot > 0.03 and level > 0.05:
        st = Image.new("RGBA", (220, 200), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        for j in range(3):
            pts = []
            for k in range(14):
                yv = 190 - k * 12
                xv = 60 + j * 50 + 12 * math.sin(k * 0.6 + t * 3 + j)
                pts.append((xv, yv))
            sd.line(pts, fill=(230, 232, 240, int(170 * hot)), width=6, joint="curve")
        st = st.filter(ImageFilter.GaussianBlur(3))
        im.alpha_composite(st, (int(cx - 110), int(ty - 70 - 50 * level - 190)))


def flash(im, t):
    for s in SHOTS:
        if s <= t < s + 0.14:
            k = 1 - (t - s) / 0.14
            fl = Image.new("RGBA", (W, PH), (255, 255, 255, int(70 * k)))
            im.alpha_composite(fl)


def prop_draw(d, pts, prop, t):
    ink = INK + (255,)
    hx, hy = pts["hr"]
    if prop == "phone":
        d.rounded_rectangle([hx - 10, hy - 22, hx + 12, hy + 16], 4, fill=(30, 32, 40, 255), outline=(200, 204, 214, 255),
                            width=3)
    elif prop == "fork":
        hx, hy = pts["hl"]
        d.line([(hx, hy), (hx + 26, hy - 12)], fill=(200, 204, 214, 255), width=4)


def widget(d, y, label, value, col):
    bx = 790
    d.rounded_rectangle([bx, y, bx + 260, y + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, bx + 130, y + 10, label, font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
    spaced(d, bx + 130, y + 38, value, font(MONO, 40), col + (255,), 1)


ROOM = None
FRAME0 = None


def person_sprite(pts, body, far):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, 1)
    return cv.done()


def panel(t, hot):
    im = ROOM.copy()
    d = ImageDraw.Draw(im)
    if hot:
        pose, hip, prop = eater(t)
        level = 1 - smooth(prog(t, T_EAT0 + 0.3, T_EAT1))
        warm = 1.0
    else:
        pose, hip, prop = shooter(t)
        level = 1 - 0.12 * smooth(prog(t, T_BITE + 0.3, T_BITE + 0.8))
        warm = 1 - smooth(prog(t, 2.0, 10.5))
    bowl(im, d, t, level, warm)
    pts = AJ.place(pose, hip, 1, SC)
    body, far = (HOT_C, HOT_FAR) if hot else (PIC_C, PIC_FAR)
    spr, off = person_sprite(pts, body, far)
    if hot:
        im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    table_front(d)
    prop_draw(d, pts, prop, t)
    if hot:
        if t < T_EAT1:
            widget(d, 100, "FOOD TEMP", "68°C", (255, 150, 80))
        else:
            widget(d, 100, "EATEN", "HOT", (120, 230, 150))
    else:
        tc = temp_c(t)
        col = PW.lerp_c((255, 150, 80), (120, 180, 255), prog(tc, 68, 19))
        widget(d, 100, "FOOD TEMP", f"{int(round(tc))}°C", col)
        widget(d, 206, "PHOTOS", str(photos(t)), (240, 240, 244))
        if t >= T_POST:
            k = smooth(prog(t, T_LIKES, T_LIKES + 0.3))
            widget(d, 312, "POSTED", f"{int(3 * k)} LIKES" if t >= T_LIKES else "...", (240, 120, 160))
        flash(im, t)
    OC.speech_at(im, t, BUB_BOTH + (BUB_HOT if hot else BUB_PIC), pts)
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
        spaced(d, W / 2, TOP_Y0 + 14, "EATS IT HOT", fl, (240, 242, 248, 255), 10)
    spaced(d, W / 2, BOT_Y0 + 14, "PHOTOGRAPHS IT FIRST", fl, (220, 224, 232, 255), 10)
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
    t_end = T_BITE
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
    # camera shutter clicks
    for s in SHOTS:
        mix_in(fx, noise(0.05, int(s * 100), lo=2000, hi=8000) * env(int(0.05 * SR), 0.001, 0.02), s, 0.07, 0.3)
        mix_in(fx, noise(0.04, int(s * 100) + 1, lo=1500, hi=6000) * env(int(0.04 * SR), 0.001, 0.015), s + 0.07, 0.05,
               0.3)
    # spoon on the bowl (top)
    for tk in np.arange(T_EAT0 + 0.35, T_EAT1, 0.75):
        mix_in(fx, tone(2400, 0.12, (1, 0.4, 0.2), a=0.001, d=0.05), tk, 0.025, -0.3)
    # post whoosh, likes
    mix_in(fx, noise(0.35, 77, lo=600, hi=4000) * env(int(0.35 * SR), 0.1, 0.2), T_POST, 0.05)
    for j in range(3):
        mix_in(fx, tone(1046 + 200 * j, 0.1, (1, 0.3), a=0.002, d=0.06), T_LIKES + 0.1 * j, 0.04, 0.2)
    for k, m in enumerate((48, 55, 60, 64)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), 14.6, 0.05, (k - 1.5) * 0.4)
    for j, m in enumerate((76, 72, 67, 72)):
        mix_in(mus, OC.piano(midi(m), 1.3, 0.5), 15.0 + j * 0.5, 0.05, 0.2)
    for b0, b1, s, w in BUB_BOTH + BUB_HOT + BUB_PIC:
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
    out = sys.argv[1] if len(sys.argv) > 1 else "cold-food.mp4"
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
