#!/usr/bin/env python3
"""IDEAS.md #4 - REPLIES "K" vs WRITES A PARAGRAPH. Split screen, the channel's current style, 18 s, loops.

The same text to both at 18:00: "WANNA GRAB FOOD LATER?" Above, he answers "k" in a second, puts the phone down,
eats chips, watches TV, falls asleep. Below, he types... and types: the draft grows, a WORDS box counts up; "TOO
NEEDY." - all of it deleted; typed again, longer, with emojis; at 18:47 he sends a wall of blue: 412 words.
"..." - the answer comes: "k".
"HE WROTE AN ESSAY. / HE GOT A LETTER."  FOLLOW FOR MORE.

    python3 stick/k_reply.py stick/k-reply.mp4
    ONLY_FRAMES=0.6,1.4,3.6,4.6,7.5,10.6,11.8,13.0,13.8,15.6 python3 stick/k_reply.py /tmp/kr
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
K_GUY, K_FAR = AJ.DOER, AJ.DOER_FAR
ESSAY, ESSAY_FAR = AJ.OT, AJ.OT_FAR
RED, BLUE = (255, 64, 56), (64, 140, 255)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
HIP = OC.HIP
CHAT = (600, 56, 1050, 620)             # the chat window drawn beside each of them

# ---------------------------------------------------------------- timeline
T_MSG = 0.5
T_K = 1.15                               # "k", sent
T_CLOCK0, T_CLOCK1 = 1.2, 11.6           # 18:00 -> 18:47
T_DEL0, T_DEL1 = 4.5, 5.0
T_SEND = 11.6
T_DOTS0, T_DOTS1 = 12.2, 13.0
T_REPLY = 13.0
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "HE WROTE AN ESSAY.", "HE GOT A LETTER."
T_FOLLOW = 16.95
FRIEND_MSG = "WANNA GRAB FOOD LATER?"
DRAFT = ["Hey!! Yeah I'd love to,", "honestly I was just", "thinking about food lol.", "Where do you want to go?",
         "I'm fine with anything", "but maybe not sushi", "again haha. Also sorry", "I didn't reply sooner,",
         "I was cleaning. Should I", "bring anything? Let me", "know!! :) :) see you!!"]
BUB_ESSAY = [(4.55, 5.4, "TOO NEEDY.", "me"), (13.4, 14.8, "...", "me")]


def draft_lines(t):
    if t < 1.3:
        return 0.0
    if t < T_DEL0:
        return 5.0 * prog(t, 1.3, T_DEL0)
    if t < T_DEL1:
        return 5.0 * (1 - prog(t, T_DEL0, T_DEL1))
    if t < T_SEND:
        return len(DRAFT) * prog(t, T_DEL1 + 0.2, T_SEND - 0.3)
    return len(DRAFT)


def words(t):
    if t >= T_SEND:
        return 412
    return int(draft_lines(t) * 37)


def clock_minutes(t):
    return int(18 * 60 + 47 * prog(t, T_CLOCK0, T_CLOCK1) ** 1.05)


# ---------------------------------------------------------------- poses
SIT = OC.SIT
SIT_PHONE = OC.SIT_PHONE
CHIPS = dict(AJ.SIT_TYPE, el=(30, -60), hl=(54, -40), er=(30, -100), hr=(18, -132))
LIE = OC.LIE
FACE = dict(AJ.SIT_TYPE, head=(30, -132), neck=(20, -96), el=(50, -110), hl=(30, -140), er=(46, -106), hr=(26, -136))


def k_guy(t):
    if t < T_K + 0.4:
        return SIT_PHONE, HIP, "phone"
    if t < 6.0:
        k = 0.5 + 0.5 * math.sin(t * 4)
        return lerp_pose(SIT, CHIPS, k), HIP, "chips"
    k = smooth(prog(t, 6.0, 6.7))
    hip = (lerp(HIP[0], 420, k), lerp(HIP[1], OC.SEAT - 26, k))
    return lerp_pose(SIT, LIE, k), hip, ("sleep" if t > 8.0 else None)


def essay(t):
    if t < T_REPLY + 0.3:
        p = dict(SIT_PHONE)
        j = 3 * math.sin(t * 22)
        p["hl"] = (p["hl"][0], p["hl"][1] - abs(j))
        p["hr"] = (p["hr"][0], p["hr"][1] - abs(math.cos(t * 19)) * 3)
        return p, HIP, "phone"
    k = smooth(prog(t, T_REPLY + 0.3, T_REPLY + 0.7))
    return lerp_pose(SIT_PHONE, FACE, k), HIP, "phone" if k < 0.5 else None


# ---------------------------------------------------------------- the chat window
def chat(im, t, top):
    ink = INK + (255,)
    x0, y0, x1, y1 = CHAT
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(18, 20, 26, 255), outline=(70, 74, 86, 255), width=4)
    d.rectangle([x0 + 4, y0 + 4, x1 - 4, y0 + 64], fill=(28, 30, 38, 255))
    d.ellipse([x0 + 18, y0 + 14, x0 + 54, y0 + 50], fill=(110, 170, 120, 255))
    d.text((x0 + 68, y0 + 18), "SAM", font=font("Inter-Bold.otf", 26), fill=(240, 240, 244, 255))
    f = font(MONO, 22)
    y = y0 + 84
    if t >= T_MSG:
        a = int(255 * smooth(prog(t, T_MSG, T_MSG + 0.2)))
        w = f.getlength(FRIEND_MSG) + 30
        d.rounded_rectangle([x0 + 16, y, x0 + 16 + w, y + 46], 18, fill=(56, 58, 68, a))
        d.text((x0 + 31, y + 11), FRIEND_MSG, font=f, fill=(240, 240, 244, a))
    y += 64
    if top:
        if t >= T_K:
            a = int(255 * smooth(prog(t, T_K, T_K + 0.15)))
            d.rounded_rectangle([x1 - 76, y, x1 - 16, y + 46], 18, fill=BLUE + (a,))
            d.text((x1 - 54, y + 8), "k", font=font("Inter-Bold.otf", 26), fill=(255, 255, 255, a))
            if t > T_K + 0.6:
                d.text((x1 - 90, y + 52), "Read", font=font("Inter-Regular.otf", 16), fill=(150, 150, 160, 255))
        return
    # below: the draft in the input box, or the sent wall, then "..." and "k"
    n = draft_lines(t)
    lh = 30
    if t < T_SEND:
        full = int(n)
        frac = n - full
        bh = max(54, 24 + lh * (full + (1 if frac > 0.05 else 0)))
        by1 = y1 - 16
        by0 = by1 - bh
        d.rounded_rectangle([x0 + 14, by0, x1 - 14, by1], 18, fill=(34, 36, 44, 255), outline=(80, 84, 96, 255), width=2)
        start = 0 if t < T_DEL0 else 0
        for i in range(full + 1):
            if i >= len(DRAFT):
                break
            s = DRAFT[i]
            if i == full:
                s = s[:int(len(s) * frac)]
            d.text((x0 + 30, by0 + 12 + i * lh), s, font=f, fill=(230, 230, 236, 255))
        if int(t * 3) % 2 == 0:
            cx = x0 + 30 + (f.getlength(DRAFT[min(full, len(DRAFT) - 1)][:int(len(DRAFT[min(full, len(DRAFT) - 1)]) * frac)])
                            if full < len(DRAFT) else 0)
            d.rectangle([cx + 2, by0 + 14 + full * lh, cx + 5, by0 + 36 + full * lh], fill=(120, 170, 255, 255))
        return
    u = smooth(prog(t, T_SEND, T_SEND + 0.3))
    lh = 26
    bh = 24 + lh * len(DRAFT)
    by0 = lerp(y1 - 16 - bh, y, u)
    d.rounded_rectangle([x0 + 40, by0, x1 - 14, by0 + bh], 18, fill=BLUE + (255,))
    for i, s in enumerate(DRAFT):
        d.text((x0 + 56, by0 + 12 + i * lh), s, font=f, fill=(255, 255, 255, 255))
    ry = by0 + bh + 16
    if T_DOTS0 <= t < T_DOTS1:
        d.rounded_rectangle([x0 + 16, ry, x0 + 100, ry + 42], 18, fill=(56, 58, 68, 255))
        for j in range(3):
            a = 120 + int(135 * (0.5 + 0.5 * math.sin(t * 10 - j)))
            d.ellipse([x0 + 34 + j * 20, ry + 16, x0 + 44 + j * 20, ry + 26], fill=(220, 220, 230, a))
    if t >= T_REPLY:
        a = int(255 * smooth(prog(t, T_REPLY, T_REPLY + 0.15)))
        pop = out_back(prog(t, T_REPLY, T_REPLY + 0.25))
        d.rounded_rectangle([x0 + 16, ry, x0 + 16 + 76 * pop, ry + 62], 22, fill=(56, 58, 68, a))
        if pop > 0.8:
            d.text((x0 + 42, ry + 8), "k", font=font("Inter-Bold.otf", 38), fill=(255, 255, 255, a))


def person_sprite(pts, body, far, prop, t):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, 1)
    P = cv.P
    k = AJ.SS
    ink = INK + (255,)
    if prop == "phone":
        px = (pts["hl"][0] + pts["hr"][0]) / 2
        py = (pts["hl"][1] + pts["hr"][1]) / 2
        q0, q1 = P((px - 13, py - 24)), P((px + 13, py + 24))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 5 * k, fill=(30, 34, 48, 255), outline=ink, width=3 * k)
        s0, s1 = P((px - 9, py - 19)), P((px + 9, py + 19))
        cv.d.rectangle([s0[0], s0[1], s1[0], s1[1]], fill=(140, 200, 255, 255))
    if prop == "chips":
        bx, by = pts["hl"]
        q0, q1 = P((bx - 20, by - 36)), P((bx + 20, by + 10))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 6 * k, fill=(230, 80, 60, 255), outline=ink, width=3 * k)
    return cv.done()


ROOM = None
FRAME0 = None


def panel(t, top):
    im = ROOM.copy()
    if top:
        pose, hip, prop = k_guy(t)
        body, far = K_GUY, K_FAR
    else:
        pose, hip, prop = essay(t)
        body, far = ESSAY, ESSAY_FAR
    pts = AJ.place(pose, hip, 1, SC)
    if prop == "phone":
        OC.phone_glow(im, pts, "phone")
    spr, off = person_sprite(pts, body, far, prop, t)
    if top:
        im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    if top and prop == "sleep":
        for i in range(2):
            ph = (t * 0.7 + i * 0.5) % 1.0
            hx, hy = pts["head"]
            d.text((hx + 20 + 26 * ph + i * 12, hy - 50 - 50 * ph), "z", font=font("Inter-Bold.otf", 26 + 8 * i),
                   fill=(220, 226, 240, int(255 * math.sin(math.pi * ph))))
    chat(im, t, top)
    if not top:
        OC.speech_at(im, t, BUB_ESSAY, pts)
        d = ImageDraw.Draw(im)
        bx, by = 30, 60
        d.rounded_rectangle([bx, by, bx + 200, by + 88], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
        spaced(d, bx + 100, by + 10, "WORDS", font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
        spaced(d, bx + 100, by + 36, str(words(t)), font(MONO, 40), (240, 240, 244, 255), 1)
    else:
        d = ImageDraw.Draw(im)
        bx, by = 30, 60
        d.rounded_rectangle([bx, by, bx + 200, by + 88], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
        spaced(d, bx + 100, by + 10, "WORDS", font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
        spaced(d, bx + 100, by + 36, "1" if t >= T_K else "0", font(MONO, 40), (240, 240, 244, 255), 1)
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
    fl = font("Inter-SemiBold.otf", 36)
    if t < T_L1:
        spaced(d, W / 2 - 220, TOP_Y0 + 14, "REPLIES \"K\"", fl, (240, 242, 248, 255), 6)
    spaced(d, W / 2 - 160, BOT_Y0 + 14, "WRITES A PARAGRAPH", fl, (220, 224, 232, 255), 6)
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
    ROOM = OC.build_room()


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
    figure = [74, 77, 81, 77, 74, 77, 79, 77]
    chords = [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 49, 52]]
    shifts = [0, -4, -2, -5]
    t_end = T_SEND
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
    # sent: a whoosh; "..." waiting: a held note; "k": one flat ding and a beat of quiet
    mix_in(fx, noise(0.35, 41, lo=800, hi=6000) * env(int(0.35 * SR), 0.05, 0.1), T_SEND, 0.1, 0.3)
    mix_in(mus, GS.pad(midi(62), T_REPLY - T_SEND, 0.2, 0.3), T_SEND + 0.2, 0.05)
    mix_in(fx, OC.piano(midi(72), 0.6, 0.3), T_REPLY, 0.1, 0.3)
    mix_in(fx, OC.piano(midi(84), 0.4, 0.3), T_MSG, 0.06)
    mix_in(fx, OC.piano(midi(79), 0.4, 0.3), T_K, 0.06, -0.3)
    # typing: soft clicks while he writes; backspace: a fast run
    for tk in np.arange(1.3, T_SEND - 0.3, 0.09):
        if not (T_DEL0 <= tk < T_DEL1):
            mix_in(fx, noise(0.02, int(tk * 1000), lo=2500, hi=8000) * env(int(0.02 * SR), 0.0005, 0.004), tk, 0.025, 0.3)
    for tk in np.arange(T_DEL0, T_DEL1, 0.04):
        mix_in(fx, noise(0.02, int(tk * 1000) + 1, lo=1500, hi=5000) * env(int(0.02 * SR), 0.0005, 0.004), tk, 0.035, 0.3)
    # chips crunching above
    for tk in np.arange(1.8, 6.0, 0.8):
        mix_in(fx, noise(0.12, int(tk * 100) + 7, lo=1500, hi=6000) * env(int(0.12 * SR), 0.002, 0.03), tk, 0.04, -0.3)
    for k, m in enumerate((50, 57, 62, 65)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), 14.6, 0.05, (k - 1.5) * 0.4)
    for b0, b1, s, w in BUB_ESSAY:
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
    out = sys.argv[1] if len(sys.argv) > 1 else "k-reply.mp4"
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
