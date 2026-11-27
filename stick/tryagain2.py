#!/usr/bin/env python3
"""TRY AGAIN v3 - every movement is real motion capture (CMU mocap DB, BVH by B. Hahne), retargeted to our figure.

baby walks (hook) - sprint - long jump - penalty - box jump - cartwheel - weightlifting - ladder - reach the bell -
backflip at sunrise.  YOU NEVER QUIT AS A KID. / WHY QUIT NOW?

    python3 stick/tryagain2.py --stills [t ...]
    python3 stick/tryagain2.py stick/tryagain.mp4
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
import mocap  # noqa
from compare import ell, line, rrect, poly, figure, place, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import hero, face, outfit, S, GOLD  # noqa
from money import put, track, compose  # noqa
from failfast import glow_ell, whip  # noqa
from tryagain import header, sunrise, SPOTS, ball, ghosts  # noqa

FPS, SR = 30, 44100
L = 2.5
D = mocap.CMU + "/"
_C = {}


def clip(name):
    if name not in _C:
        _C[name] = mocap.load(D + name + ".bvh")
    return _C[name]


def blend(a, b, k):
    return {j: (lerp(a[j][0], b[j][0], k), lerp(a[j][1], b[j][1], k)) for j in a}


def shift(p, dx=0.0, dy=0.0):
    return {j: (x + dx, y + dy) for j, (x, y) in p.items()}


def vsquash(p, k, floor=FLOOR):
    """scale the height of the body above the floor (a weaker jump)"""
    low = max(p["fl"][1], p["fr"][1])
    lift = floor - low
    return shift(p, 0, lift * (1 - k))


class Seq:
    """segments of clips played back to back; each starts where the last one left off (x), crossfaded."""

    def __init__(self, segs, x0, floor=FLOOR, scale=S, xfade=0.12):
        self.segs, self.x0, self.floor, self.scale, self.xf = segs, x0, floor, scale, xfade
        self.starts = []
        t = 0.0
        for sg in segs:
            self.starts.append(t)
            t += sg["dur"]
        self.dur = t
        self._x = None

    def _raw(self, i, u):
        sg = self.segs[i]
        c = clip(sg["clip"])
        tt = sg["t0"] + (sg["t1"] - sg["t0"]) * clamp(u / sg["dur"])
        p = c.pts(tt, x0=0, floor=self.floor, scale=self.scale * sg.get("size", 1.0), x_lock=sg.get("lock"), facing=sg.get("facing", 1))
        if sg.get("vk", 1.0) != 1.0:
            p = vsquash(p, sg["vk"], self.floor)
        if sg.get("fwd"):      # a little more forward travel than the actor had
            p = shift(p, sg["fwd"] * smooth(clamp((u / sg["dur"] - 0.3) / 0.4)), 0)
        if sg.get("rise"):     # lands on top of something
            p = shift(p, 0, -sg["rise"] * smooth(clamp((u / sg["dur"] - 0.42) / 0.22)))
        return shift(p, sg.get("dx", 0.0), sg.get("dy", 0.0))

    def _offsets(self):
        if self._x is None:
            self._x = []
            x = self.x0
            for i, sg in enumerate(self.segs):
                a = self._raw(i, 0.0)
                off = x - a["hip"][0] if not sg.get("abs") else sg.get("ax", 0.0)
                self._x.append(off)
                b = self._raw(i, sg["dur"])
                x = b["hip"][0] + off
        return self._x

    def pts(self, u):
        offs = self._offsets()
        i = 0
        for k, s0 in enumerate(self.starts):
            if u >= s0:
                i = k
        v = u - self.starts[i]
        p = shift(self._raw(i, v), offs[i])
        if i > 0 and v < self.xf:
            prev = shift(self._raw(i - 1, self.segs[i - 1]["dur"]), offs[i - 1])
            p = blend(prev, p, smooth(v / self.xf))
        return p


def seg(name, t0, t1, dur, **kw):
    return dict(clip=name, t0=t0, t1=t1, dur=dur, **kw)


RUN = "009/09_01"
FALLB = "090/90_18"     # pulled off his feet, lands on his back
DIVE = "090/90_16"      # falls forward on his face
FLIP = "090/90_12"
LJ = "083/83_42"
KICK = "010/10_01"
LIFT = "079/79_93"
LADDER = "013/13_33"
CART = "049/49_06"
VJ = "016/16_03"
BOX = "075/75_12"
CLUMSY = "091/91_15"

# ---------------------------------------------------------------- scenes: (name, final count, fail seqs, success seq, cam)
SCENES = [
    ("baby", 12,
     [[seg(CLUMSY, 4.3, 5.2, 0.55), seg(FALLB, 0.6, 1.4, 0.35)], [seg(CLUMSY, 4.3, 4.9, 0.35), seg(FALLB, 0.6, 1.4, 0.3)]],
     [seg(CLUMSY, 4.3, 7.5, 1.3)], (1.9, 580, FLOOR - 120), 420),
    ("sprint", 30,
     [[seg(RUN, 0.15, 0.8, 0.35), seg(DIVE, 2.95, 3.9, 0.5)], [seg(RUN, 0.15, 0.6, 0.25), seg(DIVE, 2.95, 3.9, 0.4)]],
     [seg(RUN, 0.15, 1.2, 0.6), seg(RUN, 0.15, 1.2, 0.6)], (1.3, 540, FLOOR - 220), 60),
    ("long", 50,
     [[seg(LJ, 1.8, 2.75, 0.5), seg(DIVE, 3.2, 3.9, 0.35)], [seg(LJ, 1.9, 2.75, 0.35), seg(DIVE, 3.2, 3.9, 0.3)]],
     [seg(LJ, 1.8, 3.6, 1.2)], (1.5, 470, FLOOR - 200), 300),
    ("kick", 70,
     [[seg(KICK, 4.1, 5.1, 0.6)], [seg(KICK, 4.2, 5.1, 0.45)]],
     [seg(KICK, 4.1, 5.4, 1.0)], (1.4, 600, FLOOR - 220), 380),
    ("box", 40,
     [[seg(BOX, 1.6, 2.6, 0.5, vk=0.6, fwd=70), seg(FALLB, 0.7, 1.4, 0.35)], [seg(BOX, 1.7, 2.6, 0.35, vk=0.6, fwd=70), seg(FALLB, 0.7, 1.4, 0.3)]],
     [seg(BOX, 1.6, 3.4, 1.1, rise=150, fwd=170)], (1.55, 430, FLOOR - 250), 290),
    ("cart", 25,
     [[seg(CART, 1.0, 2.1, 0.55), seg(FALLB, 0.8, 1.4, 0.3)], [seg(CART, 1.1, 2.1, 0.4), seg(FALLB, 0.8, 1.4, 0.3)]],
     [seg(CART, 1.0, 3.3, 1.2)], (1.45, 500, FLOOR - 220), 330),
    ("lift", 90,
     [[seg(LIFT, 2.0, 2.9, 0.4), seg(LIFT, 2.9, 2.0, 0.35)], [seg(LIFT, 2.0, 2.9, 0.3), seg(LIFT, 2.9, 2.0, 0.3)]],
     [seg(LIFT, 2.0, 3.9, 1.2)], (1.7, 540, FLOOR - 230), 540),
    ("ladder", 35,
     [[seg(LADDER, 4.2, 6.2, 0.6, lock=470)], [seg(LADDER, 4.2, 5.6, 0.45, lock=470)]],
     [seg(LADDER, 4.2, 10.0, 1.2, lock=470)], (1.3, 540, FLOOR - 330), 470),
    ("bell", 60,
     [[seg(VJ, 0.9, 2.4, 0.55, vk=0.55)], [seg(VJ, 1.0, 2.4, 0.45, vk=0.55)]],
     [seg(VJ, 0.9, 2.6, 1.1, vk=1.5)], (1.55, 560, FLOOR - 300), 560),
    ("flip", 100,
     [[seg(FLIP, 2.9, 4.6, 0.7)], [seg(FLIP, 3.2, 4.6, 0.45)]],
     [seg(FLIP, 3.0, 4.05, 0.7)], (1.6, 540, FLOOR - 260), 540),
]
T_END = L * len(SCENES)
DUR = T_END + 2.4
NF = int(round(DUR * FPS))


def fail_len(sc):
    return sum(sum(s["dur"] for s in f) for f in sc[2])


def scene_state(kind_i, u):
    name, n, fails, succ, cam, x0 = SCENES[kind_i]
    t = 0.0
    for k, f in enumerate(fails):
        d = sum(s["dur"] for s in f)
        if u < t + d:
            return name, n, "fail", Seq(f, x0), u - t, k, cam, x0
        t += d
    return name, n, "ok", Seq(succ, x0), u - t, len(fails), cam, x0


def tries_shown(i, u):
    name, n, fails = SCENES[i][0], SCENES[i][1], SCENES[i][2]
    fl = fail_len(SCENES[i])
    if u >= fl:
        return n
    return max(1, min(n - 1, int(1 + (n - 1) * (u / fl) ** 1.4)))


# ---------------------------------------------------------------- props per scene
def props(name, d, st, u, mode, p, x0):
    if name == "baby":
        mp = place(dict(PW.STAND, head=(30, -120), neck=(20, -84), el=(-50, -100), hl=(-100, -110), er=(-40, -96), hr=(-90, -104),
                        kl=(40, 6), fl=(-10, 60), kr=(-20, 54), fr=(-70, 60)), (720, FLOOR - 62 * S), -1, S)
        figure(st, mp, S, light=(0.4, -0.9))
        dd = ImageDraw.Draw(st)
        hx, hy = mp["head"]
        ell(dd, hx + 6, hy - 24, 18, 14, (60, 40, 30, 255))
        outfit(dd, mp, (190, 110, 130), -1, legs=False)
        face(dd, mp, "happy", -1, u)
    elif name == "long":
        rrect(d, (340, FLOOR - 2, 680, FLOOR + 22), 5, (200, 168, 104, 255))
        line(d, [(470, FLOOR - 70), (470, FLOOR)], (240, 200, 60, 255), 5)
        PW.spaced(d, 470 * K, (FLOOR - 92) * K, "RECORD", font("InterDisplay-Bold.otf", 20 * K), (240, 200, 60, 255), 3)
    elif name == "sprint":
        line(d, [(900, FLOOR), (900, FLOOR - 230)], (220, 220, 230, 255), 5)
        if mode == "ok" and p["hip"][0] > 900:
            line(d, [(900, FLOOR - 140), (880, FLOOR - 60)], (220, 50, 50, 255), 4)
        else:
            line(d, [(900, FLOOR - 140), (1100, FLOOR - 140)], (220, 50, 50, 255), 4)
    elif name == "kick":
        gx = 760
        line(d, [(gx, FLOOR), (gx, FLOOR - 250), (gx + 150, FLOOR - 220), (gx + 150, FLOOR)], (240, 240, 245, 255), 8)
        for j in range(7):
            line(d, [(gx + 4, FLOOR - 240 + j * 34), (gx + 140, FLOOR - 212 + j * 32)], (220, 220, 226, 140), 2)
    elif name == "box":
        rrect(d, (400, FLOOR - 150, 560, FLOOR), 6, (120, 84, 56, 255), outline=(70, 50, 34, 255), w=3)
    elif name == "ladder":
        for x in (430, 520):
            line(d, [(x, FLOOR), (x, FLOOR - 760)], (150, 120, 80, 255), 9)
        for k in range(1, 15):
            line(d, [(430, FLOOR - k * 52), (520, FLOOR - k * 52)], (150, 120, 80, 255), 7)
    elif name == "bell":
        bx, by = 600, FLOOR - 430
        line(d, [(bx, by - 120), (bx, by - 30)], (120, 120, 130, 255), 4)
        rr = 0.0
        if mode == "ok" and u > 0.55:
            rr = 0.5 * math.sin((u - 0.55) * 30) * math.exp(-(u - 0.55) * 3)
        c_, s_ = math.cos(rr), math.sin(rr)
        pts = [(-34, 0), (34, 0), (24, -50), (-24, -50)]
        poly(d, [(bx + px * c_ - py * s_, by + px * s_ + py * c_) for px, py in pts], (240, 200, 60, 255))
        line(d, [(bx - 40, FLOOR - 360), (bx + 40, FLOOR - 360)], (240, 200, 60, 140), 3)


def weights(d, p):
    hx = (p["hl"][0] + p["hr"][0]) / 2
    hy = (p["hl"][1] + p["hr"][1]) / 2
    line(d, [(hx - 170, hy), (hx + 170, hy)], (192, 196, 206, 255), 7)
    for x in (hx - 160, hx - 140, hx + 140, hx + 160):
        rrect(d, (x - 8, hy - 44, x + 8, hy + 44), 3, (40, 42, 50, 255), outline=(110, 114, 128, 255), w=1.5)


def frame(t):
    if t >= T_END:
        u = t - T_END
        st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        d = ImageDraw.Draw(st)
        props("baby", d, st, 0, "ok", None, 0)
        p = Seq([seg(CLUMSY, 7.4, 7.5, 1.0, size=0.6)], 640).pts(0.5)
        baby(st, p, "laugh", u)
        im = compose(st, None, 1.9, 600, FLOOR - 120, spots=SPOTS, refl=True)
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
    i = min(len(SCENES) - 1, int(t / L))
    u = t - i * L
    name, n, mode, seq, v, k, cam, x0 = scene_state(i, u)
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    size = 0.6 if name == "baby" else 1.0
    for sg in seq.segs:
        sg.setdefault("size", size)
    p = seq.pts(min(v, seq.dur))
    props(name, d, st, v, mode, p, x0)
    if name == "flip" and mode == "ok" and v > seq.dur - 0.25:     # land it on his feet
        stand = place(PW.STAND, (p["hip"][0], FLOOR - 113 * S), 1, S)
        p = blend(p, stand, smooth((v - (seq.dur - 0.25)) / 0.25))
    if name == "flip" and mode == "ok" and v >= seq.dur:
        p = place(PW.ARMS_UP, (p["hip"][0], FLOOR - 113 * S), 1, S)
    expr = "happy" if mode == "ok" and v > seq.dur * 0.6 else ("determined" if v < seq.dur * 0.5 else "shocked")
    if name == "baby":
        baby(st, p, "laugh" if mode == "ok" or v > seq.dur * 0.6 else "determined", t)
    else:
        hero(st, p, "plain", 1, expr, t)
    if name == "lift":
        weights(d, p)
    if name == "kick":
        b0 = (seq.pts(seq.dur * (0.55 if mode == 'fail' else 0.45))['fr'][0] + 24, FLOOR - 22)
        hit = 0.55 if mode == "fail" else 0.45
        w = clamp((v - seq.dur * hit) / (seq.dur * 0.35))
        tgt = {0: (760, FLOOR - 250), 1: (900, FLOOR - 420)}.get(k, (790, FLOOR - 220))
        bx, by = lerp(b0[0], tgt[0], w), lerp(b0[1], tgt[1], w) - 100 * 4 * w * (1 - w)
        if mode == "fail" and w >= 1:
            bx, by = tgt[0] - 120 * clamp((v - seq.dur * 0.9) * 8), tgt[1] + 200 * clamp((v - seq.dur * 0.9) * 8)
        ball(d, bx, by, v * 10, col=(240, 240, 240))
    done = mode == "ok"
    s_at = fail_len(SCENES[i])
    shake = 10 * max(0, 1 - (u - s_at) / 0.25) if done and u < s_at + 0.25 else 0
    z, cx, cy = cam
    back = sunrise(smooth(prog(u, s_at - 0.2, s_at + 0.6))) if name == "flip" else None
    im = compose(st, None, z * (0.96 + 0.08 * u / L), cx + shake * math.sin(t * 80), cy, spots=SPOTS, back=back, refl=True)
    if done and u < s_at + 0.4:
        im.alpha_composite(Image.new("RGBA", im.size, (255, 220, 140, int(55 * (1 - (u - s_at) / 0.4)))))
    if abs(u) < 0.12 and i > 0:
        im = whip(im, 1 - abs(u) / 0.12)
    elif abs(u - L) < 0.12:
        im = whip(im, 1 - abs(u - L) / 0.12)
    header(im, t, tries_shown(i, u), done, hq.pop(u, s_at, 0.2) if done else 1.0)
    return np.asarray(im.convert("RGB"))


def baby(st, p, expr, t):
    figure(st, p, S * 0.6, light=(0.4, -0.9))
    d = ImageDraw.Draw(st)
    hx, hy = p["head"]
    ell(d, hx, hy - 6, 28, 28, (238, 238, 242, 255))
    d.ellipse(((hx - 28) * K, (hy - 34) * K, (hx + 28) * K, (hy + 22) * K), outline=(28, 28, 34, 255), width=int(2.5 * K))
    line(d, [(hx - 4, hy - 34), (hx + 2, hy - 44), (hx + 8, hy - 36)], (28, 28, 34, 255), 3)
    face(d, dict(p, head=(hx, hy - 6)), expr, 1, t)


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
        s0 = i * L
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
        ts = [float(a) for a in sys.argv[2:]] or [i * L + o for i in range(10) for o in (0.4, 1.0, 2.1)]
        cols = 10
        rows = math.ceil(len(ts) / cols)
        sheet = Image.new("RGB", (180 * cols, 320 * rows))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((180, 320), Image.LANCZOS), ((j % cols) * 180, (j // cols) * 320))
        p = os.path.join(here, "tryagain", "stills.png")
        sheet.save(p)
        print(p)
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
    print(f'Credit: Music: "{MUSIC[:-4]}" by Kevin MacLeod (incompetech.com), CC BY 4.0')
    print('Motion: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu)')


if __name__ == "__main__":
    main()
