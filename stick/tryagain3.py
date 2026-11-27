#!/usr/bin/env python3
"""TRY AGAIN v4 - clear situations, all real motion capture (CMU mocap DB).

baby walk - free throw - golf - baseball - catch - hurdles - weightlifting - swimming - penalty... - backflip.
Every fall is followed by a real get-up.  YOU NEVER QUIT AS A KID. / WHY QUIT NOW?

    python3 stick/tryagain3.py --stills [t ...]
    python3 stick/tryagain3.py stick/tryagain.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import hq  # noqa
from compare import ell, line, rrect, poly, figure, place, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import hero, face, outfit, S, GOLD  # noqa
from money import put, track, compose  # noqa
from failfast import whip  # noqa
from tryagain import header, sunrise, SPOTS, ball  # noqa
from tryagain2 import Seq, seg, blend, shift, clip, baby, weights, FALLB, DIVE, FLIP, LIFT  # noqa

FPS, SR = 30, 44100
BABY = "133/133_21"
GETUP = "140/140_01"
FREE = "124/124_04"
GOLF = "064/64_01"
BAT = "124/124_07"
CATCH = "033/33_01"
HURDLE = "127/127_25"
SWIM = "125/125_06"
TAIL = 0.45


def up(d=0.6):
    return seg(GETUP, 1.7, 4.6, d)


# (name, final count, [fail attempts], success, camera, x0)
SCENES = [
    ("baby", 12, [[seg(BABY, 0.3, 1.3, 0.45), seg(FALLB, 0.6, 1.4, 0.3)], [seg(BABY, 0.3, 1.0, 0.35), seg(FALLB, 0.6, 1.4, 0.3)]],
     [seg(BABY, 0.3, 3.5, 1.2)], (1.9, 560, FLOOR - 120), 380),
    ("free", 30, [[seg(FREE, 3.6, 5.2, 0.75)], [seg(FREE, 3.7, 5.2, 0.6)]],
     [seg(FREE, 3.6, 5.6, 1.1)], (1.45, 640, FLOOR - 260), 380),
    ("golf", 45, [[seg(GOLF, 1.3, 3.5, 0.8)], [seg(GOLF, 1.6, 3.5, 0.6)]],
     [seg(GOLF, 1.3, 3.6, 1.15)], (1.35, 600, FLOOR - 220), 300),
    ("bat", 20, [[seg(BAT, 2.7, 4.4, 0.7)], [seg(BAT, 2.9, 4.4, 0.55)]],
     [seg(BAT, 2.7, 4.8, 1.1)], (1.5, 560, FLOOR - 220), 460),
    ("catch", 25, [[seg(CATCH, 3.9, 6.0, 0.75)], [seg(CATCH, 4.1, 6.0, 0.6)]],
     [seg(CATCH, 3.9, 6.4, 1.1)], (1.5, 560, FLOOR - 230), 460),
    ("hurdle", 40, [[seg(HURDLE, 0.15, 0.72, 0.38), seg(DIVE, 2.95, 3.9, 0.4), up(0.55)], [seg(HURDLE, 0.15, 0.72, 0.32), seg(DIVE, 2.95, 3.9, 0.35)]],
     [seg(HURDLE, 0.15, 1.8, 1.0)], (1.3, 560, FLOOR - 220), 140),
    ("lift", 90, [[seg(LIFT, 2.0, 2.9, 0.4), seg(LIFT, 2.9, 2.0, 0.35)], [seg(LIFT, 2.0, 2.9, 0.3), seg(LIFT, 2.9, 2.0, 0.3)]],
     [seg(LIFT, 2.0, 3.9, 1.2)], (1.7, 540, FLOOR - 230), 540),
    ("swim", 60, [[seg(SWIM, 9.0, 11.0, 0.8)], [seg(SWIM, 9.0, 10.5, 0.6)]],
     [seg(SWIM, 9.0, 14.0, 1.3)], (1.3, 600, FLOOR - 120), 160),
    ("flip", 100, [[seg(FLIP, 2.9, 4.6, 0.7), up(0.55)], [seg(FLIP, 3.2, 4.6, 0.45)]],
     [seg(FLIP, 3.0, 4.05, 0.7)], (1.6, 540, FLOOR - 260), 540),
]


def fail_len(sc):
    return sum(sum(s["dur"] for s in f) for f in sc[2])


def scene_len(sc):
    return fail_len(sc) + sum(s["dur"] for s in sc[3]) + TAIL


STARTS = []
_t = 0.0
for _sc in SCENES:
    STARTS.append(_t)
    _t += scene_len(_sc)
T_END = _t
DUR = T_END + 2.5
NF = int(round(DUR * FPS))


def scene_at(t):
    i = 0
    for k, s0 in enumerate(STARTS):
        if t >= s0:
            i = k
    return i, t - STARTS[i]


def state(i, u):
    name, n, fails, succ, cam, x0 = SCENES[i]
    size = 0.6 if name == "baby" else 1.0
    t = 0.0
    for k, f in enumerate(fails):
        d = sum(s["dur"] for s in f)
        if u < t + d:
            return "fail", Seq([dict(s, size=size) for s in f], x0), u - t, k
        t += d
    return "ok", Seq([dict(s, size=size) for s in succ], x0), u - t, len(fails)


def when(seq, name, ct):
    """sequence time at which clip `name` reaches clip time ct (first segment that contains it)"""
    for s0, sg in zip(seq.starts, seq.segs):
        if sg["clip"] == name and min(sg["t0"], sg["t1"]) <= ct <= max(sg["t0"], sg["t1"]):
            return s0 + sg["dur"] * (ct - sg["t0"]) / (sg["t1"] - sg["t0"])
    return None


def hand_mid(p):
    return ((p["hl"][0] + p["hr"][0]) / 2, (p["hl"][1] + p["hr"][1]) / 2)


def arc(a, b, w, h):
    return lerp(a[0], b[0], w), lerp(a[1], b[1], w) - h * 4 * w * (1 - w)


def unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


# ---------------------------------------------------------------- props
HOOP_X, RIM_Y = 860, FLOOR - 430


def hoop(d, swish=0.0):
    line(d, [(980, FLOOR), (980, FLOOR - 520)], (90, 94, 104, 255), 12)
    rrect(d, (940, FLOOR - 560, 956, FLOOR - 380), 3, (230, 232, 240, 255))
    for j in range(5):
        x0 = HOOP_X - 50 + j * 22
        line(d, [(x0, RIM_Y), (HOOP_X - 26 + j * 13 + 6 * swish * math.sin(j * 3), RIM_Y + 70 + 10 * swish)], (236, 236, 240, 220), 2)
    line(d, [(HOOP_X - 54, RIM_Y), (942, RIM_Y)], (236, 96, 40, 255), 8)


def props_and_ball(name, d, st, mode, seq, v, k, p):
    if name == "baby":
        mp = place(dict(PW.STAND, head=(30, -120), neck=(20, -84), el=(-50, -100), hl=(-100, -110), er=(-40, -96), hr=(-90, -104),
                        kl=(40, 6), fl=(-10, 60), kr=(-20, 54), fr=(-70, 60)), (760, FLOOR - 62 * S), -1, S)
        figure(st, mp, S, light=(0.4, -0.9))
        dd = ImageDraw.Draw(st)
        hx, hy = mp["head"]
        ell(dd, hx + 6, hy - 24, 18, 14, (60, 40, 30, 255))
        outfit(dd, mp, (190, 110, 130), -1, legs=False)
        face(dd, mp, "happy", -1, v)
        return
    if name == "free":
        tr = when(seq, FREE, 4.45)
        sw = smooth(clamp((v - tr - 0.45) / 0.1)) * (1 - smooth(clamp((v - tr - 0.6) / 0.3))) if mode == "ok" else 0
        hoop(d, sw)
        if v < tr:
            bx, by = hand_mid(p)
            by -= 26
        else:
            rel = seq.pts(tr)
            a = (hand_mid(rel)[0], hand_mid(rel)[1] - 26)
            w = clamp((v - tr) / 0.45)
            tgt = (HOOP_X, RIM_Y - 26) if mode == "ok" else ((HOOP_X - 54, RIM_Y - 20) if k == 0 else (HOOP_X + 70, RIM_Y - 60))
            bx, by = arc(a, tgt, w, 170)
            if v > tr + 0.45:
                w2 = clamp((v - tr - 0.45) / 0.35)
                if mode == "ok":
                    bx, by = tgt[0], lerp(tgt[1], FLOOR - 24, w2)
                else:
                    bx, by = lerp(tgt[0], tgt[0] - 220 * (1 if k == 0 else -0.3), w2), lerp(tgt[1], FLOOR - 24, w2 ** 0.8)
        ball(d, bx, by, v * 9)
        return
    if name == "golf":
        hole = 980
        line(d, [(hole, FLOOR), (hole, FLOOR - 200)], (220, 220, 226, 255), 4)
        poly(d, [(hole, FLOOR - 200), (hole + 60, FLOOR - 182), (hole, FLOOR - 164)], (220, 50, 50, 255))
        ell(d, hole, FLOOR + 2, 16, 4, (10, 10, 12, 255))
        hm = hand_mid(p)
        ux, uy = unit(p["neck"], hm)
        head = (hm[0] + ux * 110, hm[1] + uy * 110)
        line(d, [hm, head], (200, 200, 210, 255), 4)
        rrect(d, (head[0] - 12, head[1] - 6, head[0] + 12, head[1] + 6), 3, (60, 60, 70, 255))
        tr = when(seq, GOLF, 2.72)
        p0 = seq.pts(0.0)
        hm0 = hand_mid(p0)
        u0 = unit(p0["neck"], hm0)
        b0 = (hm0[0] + u0[0] * 110 + 14, FLOOR - 8)
        if v < tr:
            bx, by = b0
        else:
            land = {0: hole - 260, 1: hole + 260}.get(k, hole - 40) if mode == "fail" else hole - 40
            w = clamp((v - tr) / 0.5)
            bx, by = arc(b0, (land, FLOOR - 8), w, 420)
            if v > tr + 0.5 and mode == "ok":
                w2 = clamp((v - tr - 0.5) / 0.25)
                bx, by = lerp(land, hole, w2), FLOOR - 8 + 10 * smooth(clamp((w2 - 0.85) / 0.15))
        ell(d, bx, by, 8, 8, (248, 248, 248, 255))
        return
    if name == "bat":
        hm = hand_mid(p)
        ux, uy = unit(p["er"], p["hr"])
        tip = (hm[0] + ux * 130, hm[1] + uy * 130)
        line(d, [hm, tip], (170, 120, 70, 255), 9)
        tc = when(seq, BAT, 3.45)
        pc = seq.pts(tc)
        front = pc["hip"][0] + 90
        hit = (front, FLOOR - 170)
        start = (W + 80, FLOOR - 190)
        if v < tc:
            w = clamp((v - (tc - 0.4)) / 0.4)
            bx, by = arc(start, hit, w, 30) if w > 0 else (W + 200, 0)
        elif mode == "fail":
            w = clamp((v - tc) / 0.3)
            bx, by = lerp(hit[0], hit[0] - 600, w), lerp(hit[1], hit[1] + 30, w)
        else:
            w = clamp((v - tc) / 0.5)
            bx, by = lerp(hit[0], W + 300, w), lerp(hit[1], -500, w)
        ell(d, bx, by, 11, 11, (250, 250, 250, 255))
        return
    if name == "catch":
        segc = seq.segs[0]
        ts = np.linspace(0, segc["dur"], 40)
        ys = [hand_mid(seq.pts(x))[1] for x in ts]
        tc = float(ts[int(np.argmin(ys))])
        start = (W + 60, FLOOR - 640)
        hc = hand_mid(seq.pts(tc))
        if v < tc:
            w = clamp((v - (tc - 0.55)) / 0.55)
            bx, by = arc(start, hc, w, 120) if w > 0 else (W + 200, 0)
        elif mode == "fail":
            w = clamp((v - tc) / 0.4)
            bx, by = lerp(hc[0], hc[0] - 120, w), lerp(hc[1], FLOOR - 20, w ** 0.7)
        else:
            bx, by = hand_mid(p)
        ell(d, bx, by, 26, 15, (150, 80, 40, 255))
        line(d, [(bx - 10, by), (bx + 10, by)], (240, 240, 240, 255), 2)
        return
    if name == "hurdle":
        ref = Seq([dict(s) for s in SCENES[5][3]], SCENES[5][5])
        hx = ref.pts(when(ref, HURDLE, 0.9))["hip"][0] + 10
        tilt = 0.0
        if mode == "fail" or (k > 0 and mode == "ok" and False):
            tk = when(seq, DIVE, 3.0)
            tilt = 1.3 * smooth(clamp((v - (tk or 99)) / 0.25)) if tk is not None else 0
        c_, s_ = math.cos(tilt), math.sin(tilt)
        top = (hx + 150 * s_, FLOOR - 150 * c_)
        line(d, [(hx, FLOOR), top], (230, 230, 236, 255), 6)
        line(d, [(top[0] - 18 * c_, top[1] - 18 * s_), (top[0] + 18 * c_, top[1] + 18 * s_)], (230, 60, 50, 255), 12)
        line(d, [(hx - 30, FLOOR), (hx + 30, FLOOR)], (230, 230, 236, 255), 5)
        return
    if name == "lift":
        weights(d, p)
        return
    if name == "swim":
        line(d, [(960, FLOOR - 160), (960, FLOOR + 60)], (220, 220, 226, 255), 8)
        rrect(d, (950, FLOOR - 200, 1010, FLOOR - 160), 4, GOLD + (255,))
        return


def water(st, t, sink_bubbles=None):
    lay = Image.new("RGBA", st.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    top = FLOOR - 70
    d.rectangle((0, top * K, W * K, (FLOOR + 80) * K), (40, 110, 190, 150))
    pts = [(x, top + 5 * math.sin(x / 40 + t * 4)) for x in range(-10, W + 20, 20)]
    line(d, pts, (170, 220, 255, 220), 3)
    if sink_bubbles:
        x, y, w = sink_bubbles
        for j in range(6):
            yy = y - 120 * ((w * 2 + j / 6) % 1)
            ell(d, x + 10 * math.sin(j * 2 + t * 5), yy, 5, 5, (220, 240, 255, 200))
    st.alpha_composite(lay)


def frame(t):
    if t >= T_END:
        u = t - T_END
        st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        d = ImageDraw.Draw(st)
        props_and_ball("baby", d, st, "ok", None, 0, 0, None)
        p = Seq([seg(BABY, 3.4, 3.5, 1.0, size=0.6)], 680).pts(0.5)
        baby(st, p, "laugh", u)
        im = compose(st, None, 1.9, 640, FLOOR - 120, spots=SPOTS, refl=True)
        f = font("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", 66)
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        for j, (s_, col, t0) in enumerate((("YOU NEVER QUIT", (246, 240, 226), 0.0), ("AS A KID.", (246, 240, 226), 0.15),
                                            ("WHY QUIT NOW?", GOLD, 0.9))):
            a = smooth(prog(u, t0, t0 + 0.35))
            if a > 0:
                PW.spaced(ld, W / 2, 220 + j * 90 + (40 if j == 2 else 0), s_, f, col + (int(255 * a),), 5)
        im.alpha_composite(lay)
        return np.asarray(im.convert("RGB"))
    i, u = scene_at(t)
    name, n, fails, succ, cam, x0 = SCENES[i]
    mode, seq, v, k = state(i, u)
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    p = seq.pts(min(v, seq.dur))
    if name == "swim":                          # the clip swims in place: carry him forward, in the water
        go = (260 if mode == "fail" else 650) * clamp(v / seq.dur) * (0.55 if mode == "fail" else 1.0)
        p = shift(p, go, 58)
    if name == "swim" and mode == "fail":       # stops, sinks
        w = smooth(clamp((v - seq.dur * 0.55) / (seq.dur * 0.45)))
        p = shift(p, 0, 110 * w)
    if name == "baby" and mode == "ok":         # all the way to mom
        p = shift(p, 160 * smooth(clamp(v / seq.dur)), 0)
    if name == "flip" and mode == "ok":
        stand = place(PW.STAND, (p["hip"][0], FLOOR - 113 * S), 1, S)
        p = blend(p, stand, smooth(clamp((v - (seq.dur - 0.25)) / 0.25)))
        if v >= seq.dur:
            p = place(PW.ARMS_UP, (p["hip"][0], FLOOR - 113 * S), 1, S)
    if name != "catch":
        props_and_ball(name, d, st, mode, seq, v, k, p)
    late = v > seq.dur * 0.55
    expr = "happy" if mode == "ok" and late else ("shocked" if mode == "fail" and late else "determined")
    if name == "baby":
        baby(st, p, "laugh" if mode == "ok" or late else "determined", t)
    else:
        hero(st, p, "plain", 1, expr, t)
    if name == "catch":
        props_and_ball(name, ImageDraw.Draw(st), st, mode, seq, v, k, p)
    if name == "swim":
        w = smooth(clamp((v - seq.dur * 0.55) / (seq.dur * 0.45))) if mode == "fail" else 0
        water(st, t, (p["head"][0], p["head"][1], w) if w > 0 else None)
    s_at = fail_len(SCENES[i])
    done = mode == "ok"
    shake = 10 * max(0, 1 - (u - s_at) / 0.25) if done and u < s_at + 0.25 else 0
    z, cx, cy = cam
    L = scene_len(SCENES[i])
    back = sunrise(smooth(prog(u, s_at - 0.2, s_at + 0.6))) if name == "flip" else None
    im = compose(st, None, z * (0.96 + 0.08 * u / L), cx + shake * math.sin(t * 80), cy, spots=SPOTS, back=back, refl=True)
    if done and u < s_at + 0.4:
        im.alpha_composite(Image.new("RGBA", im.size, (255, 220, 140, int(55 * (1 - (u - s_at) / 0.4)))))
    if abs(u) < 0.12 and i > 0:
        im = whip(im, 1 - abs(u) / 0.12)
    elif abs(u - L) < 0.12:
        im = whip(im, 1 - abs(u - L) / 0.12)
    fl = s_at
    shown = n if u >= fl else max(1, min(n - 1, int(1 + (n - 1) * (u / fl) ** 1.4)))
    header(im, t, shown, done, hq.pop(u, s_at, 0.2) if done else 1.0)
    return np.asarray(im.convert("RGB"))


def render(i):
    acc = None
    for k in range(2):
        f = frame((i + k / 4) / FPS).astype(np.float32)
        acc = f if acc is None else acc + f
    return (acc / 2).astype(np.uint8).tobytes()


MUSIC = "Undaunted.mp3"


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    put(out, track(MUSIC, 40.0, DUR), 0.0, 1.7, fin=0.05, fout=1.0)
    thud = noise(0.22, 3, lo=60, hi=1200)[:int(0.22 * SR)] * env(int(0.22 * SR), 0.002, 0.16)
    ding = tone(880, 0.7, (1, 2, 3), a=0.002, d=0.6)
    for i, sc in enumerate(SCENES):
        s0 = STARTS[i]
        t = 0.0
        for f in sc[2]:
            t += sum(s["dur"] for s in f)
            mix_in(out, thud, s0 + t - 0.12, 0.35, 0.0)
        mix_in(out, ding, s0 + fail_len(sc), 0.32, 0.0)
        if i:
            mix_in(out, noise(0.3, 9, lo=500, hi=7000)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.15, 0.1), s0 - 0.15, 0.15, 0.0)
    mix_in(out, tone(55, 1.0, (1, 2), a=0.002, d=0.9), T_END + 0.9, 0.5, 0.0)
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.6, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]]
        if not ts:
            for i, sc in enumerate(SCENES):
                fl = fail_len(sc)
                ts += [STARTS[i] + fl * 0.3, STARTS[i] + fl * 0.8, STARTS[i] + fl + 0.5, STARTS[i] + scene_len(sc) - 0.3]
            ts.append(T_END + 1.8)
        cols = 8
        rows = math.ceil(len(ts) / cols)
        sheet = Image.new("RGB", (180 * cols, 320 * rows))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((180, 320), Image.LANCZOS), ((j % cols) * 180, (j // cols) * 320))
        p = os.path.join(here, "tryagain", "stills.png")
        sheet.save(p)
        print(p, round(DUR, 1))
        return
    out = sys.argv[1]
    wav = out + ".wav"
    write_wav(wav, audio())
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-13:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for b in pool.imap(render, range(NF), chunksize=2):
            p.stdin.write(b)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)


if __name__ == "__main__":
    main()
