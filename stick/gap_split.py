#!/usr/bin/env python3
"""ONE MORE TRY - THE GAP on a split screen: the same gap, the same planks, the same chest, two people, 22.4 s, loops.

Both look at the chest across the gap ("GOLD!"). Try 1, together: run, jump, fall in the river, climb back. Try 2,
together: one plank, too short, it tips. Then they split: above, the doer - "ONE MORE TRY." - sits, "?", a light bulb,
ties two planks with the rope, crosses, opens the chest. Below, the overthinker - "I GIVE UP." - walks back to the rock
and takes out his phone; when the gold light comes up above: "IT'S IMPOSSIBLE."  TRIES 3 above, 2 below.
"THE ONLY DIFFERENCE / WAS ONE MORE TRY."

    python3 stick/gap_split.py stick/one-more-try.mp4
    ONLY_FRAMES=0.5,2.4,6.9,9.9,11.3,13.2,15.8,20 python3 stick/gap_split.py /tmp/gs
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
import ai_job as AJ  # noqa
import the_gap as G  # noqa
from perfect_wave import MONO, clamp, env, font, lerp, lerp_pose, mix_in, noise, out_back, prog, smooth, spaced, tone  # noqa

W, H, FPS = G.W, G.H, G.FPS
DUR, NF, XFADE, SR = G.DUR, G.NF, G.XFADE, G.SR

# a shallower river so a whole scene fits in half the screen
G.RIVER = G.CT + 225
G.MOON_Y = G.CT - 380
G.J_VY = -600.0
G.T_SPLASH1, G.X_SPLASH1 = G._splash1()


def _splash2():
    tau = 0.0
    while True:
        tau += 1 / 600
        y = G.CT + 40 + 260 * tau + 0.5 * G.J_G * tau * tau
        if y > G.RIVER - 10:
            return G.T_TIP1 + tau


G.T_SPLASH2 = _splash2()
# the doer says "ONE MORE TRY." before the "?" comes
G.T_Q0, G.T_BULB, G.T_BULB1 = 10.65, 11.15, 11.75

CROP0, CROP1 = G.CT - 505, G.CT + 245      # the band of the scene each panel shows
PANEL_H = CROP1 - CROP0                    # 730
TOP_Y0, BOT_Y0 = 258, 1084
T_GIVEUP = G.T_UP2_1                       # 9.6: the overthinker is back on top after try 2
T_IMPOSSIBLE = 15.5
LINE1, LINE2 = "THE ONLY DIFFERENCE", "WAS ONE MORE TRY."
T_L1, T_L2 = G.T_L1, G.T_L2

BUB_DOER = [(0.3, 1.1, "GOLD!"), (T_GIVEUP + 0.05, G.T_Q0 - 0.05, "ONE MORE TRY.")]
BUB_OT = [(0.3, 1.1, "GOLD!"), (T_GIVEUP + 0.05, 11.4, "I GIVE UP."), (T_IMPOSSIBLE, 17.6, "IT'S IMPOSSIBLE.")]


def quitter(t):
    """Same as the doer until he is back up after try 2; then back to the rock and the phone."""
    if t < T_GIVEUP + 0.2:
        return G.doer(t)
    if t < 10.9:
        u = prog(t, T_GIVEUP + 0.2, 10.9)
        x = lerp(G.LE - 60, G.ROCK_X + 20, smooth(u))
        return G.walk(t, G.STAND), x, G.STAND_Y, -1, 0.0, 1.0, None
    hip_y = G.CT - 144
    if t < 11.3:
        k = smooth(prog(t, 10.9, 11.3))
        return lerp_pose(G.STAND, G.OT_SIT, k), G.ROCK_X + 20, lerp(G.STAND_Y, hip_y, k), 1, 0.0, 1.0, None
    k = smooth(prog(t, 11.6, 12.0))
    if T_IMPOSSIBLE - 0.3 <= t < T_IMPOSSIBLE + 2.0:
        k2 = smooth(prog(t, T_IMPOSSIBLE - 0.3, T_IMPOSSIBLE)) * (1 - smooth(prog(t, T_IMPOSSIBLE + 1.6, T_IMPOSSIBLE + 2.0)))
        return lerp_pose(G.OT_PHONE, G.OT_UP, k2), G.ROCK_X + 20, hip_y, 1, 0.0, 1.0, "phone"
    return lerp_pose(G.OT_SIT, G.OT_PHONE, k), G.ROCK_X + 20, hip_y, 1, 0.0, 1.0, "phone" if k > 0.5 else None


def tries(t, who):
    n = G.tries(t)
    return min(n, 2) if who == "ot" else n


def scene(t, who):
    """The whole scene for one person, as a full-size image; the panel is a band of it."""
    img = G.BG.copy()
    d = ImageDraw.Draw(img)
    if who == "doer":
        d = G.draw_chest(img, d, t)
        dp = G.doer(t)
        G.draw_props(d, t, dp)
    else:
        d = G.draw_chest(img, d, min(t, G.T_OPEN - 0.01) if t < G.T_OPEN else G.T_OPEN - 0.01 + 0 * t)
        dp = quitter(t)
        G.draw_props(d, min(t, T_GIVEUP), dp if t < T_GIVEUP else (G.STAND, -500, 0, 1, 0, 0.0, None))
    pose, x, y, f, rr, al, prop = dp
    pts = None
    body, far = (G.DOER, G.DOER_FAR) if who == "doer" else (G.OT, G.OT_FAR)
    if al > 0.01:
        pts = G.at_hip(pose, x, y, f, rr)
        spr, off = G.sprite(pts, body, far, f, prop=prop if prop == "phone" else None)
        if who == "doer":
            gcol = (255, 214, 120) if t >= G.T_OPEN else (210, 228, 255)
            img.alpha_composite(PW.glow_of(spr, 0.6 + 0.6 * smooth(prog(t, G.T_OPEN, G.T_OPEN + 0.4)), 14, gcol), off)
        img.alpha_composite(spr, off)
    d = ImageDraw.Draw(img)
    if G.T_STEP1 <= t < G.T_TIP1:
        ang = 1.25 * G.in_quad(prog(t, G.T_STEP1, G.T_TIP1))
        c = G.rot((G.PLANK_L / 2 - 20, -8), ang)
        G.draw_plank(d, G.LE + c[0], G.CT + c[1], ang)
    if prop == "drip" and pts:
        G.drips(d, t, pts)
    G.splash(d, t, G.T_SPLASH1, G.X_SPLASH1)
    G.splash(d, t, G.T_SPLASH2, G.LE + 120)
    if who == "doer" and pts is not None and G.T_Q0 <= t < G.T_BULB1:
        G.thought(img, d, t, pts["head"])
        d = ImageDraw.Draw(img)
    for b0, b1, s in (BUB_DOER if who == "doer" else BUB_OT):
        if b0 <= t < b1 and pts is not None:
            bs = AJ.bubble(s)
            sc = out_back(prog(t, b0, b0 + 0.18))
            a = 1 - smooth(prog(t, b1 - 0.12, b1))
            if sc < 0.05:
                continue
            spr2 = bs.resize((max(1, int(bs.width * sc)), max(1, int(bs.height * sc))), Image.LANCZOS)
            if a < 0.999:
                spr2.putalpha(spr2.split()[3].point(lambda v: int(v * a)))
            hx, hy = pts["head"]
            by = max(CROP0 + 8, hy - 56 - spr2.height)
            img.alpha_composite(spr2, (int(clamp(hx - 40, 16, W - 16 - spr2.width)), int(by)))
    return img.crop((0, CROP0, W, CROP1))


def tries_box(d, x0, y0, n, t, gold):
    bw, bh = 220, 92
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 8, fill=(18, 20, 28, 225), outline=(90, 94, 104, 255), width=2)
    spaced(d, x0 + bw / 2, y0 + 10, "TRIES", font("Inter-SemiBold.otf", 22), (190, 194, 204, 255), 6)
    ch = max([t0 for t0, k in G.TRIES if t0 <= t and k <= (3 if gold else 2)], default=-9)
    pop = math.exp(-(t - ch) * 8) if ch > 0 else 0.0
    col = PW.lerp_c((250, 250, 252), G.GOLD, pop if not (gold and n == 3) else 1.0)
    spaced(d, x0 + bw / 2, y0 + 34 - 6 * pop, str(n), font("InterDisplay-Bold.otf", int(46 * (1 + 0.2 * pop))),
           col + (255,), 0)


def frame(t):
    img = Image.new("RGBA", (W, H), (5, 6, 10, 255))
    img.alpha_composite(scene(t, "doer"), (0, TOP_Y0))
    img.alpha_composite(scene(t, "ot"), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    for y in (TOP_Y0, TOP_Y0 + PANEL_H, BOT_Y0, BOT_Y0 + PANEL_H):
        d.line([(0, y), (W, y)], fill=(40, 42, 52, 255), width=2)
    tries_box(d, W - 246, TOP_Y0 + 20, tries(t, "doer"), t, True)
    tries_box(d, W - 246, BOT_Y0 + 20, tries(t, "ot"), t, False)
    spaced(d, W / 2, TOP_Y0 - 52, "DOER", font("Inter-SemiBold.otf", 40), (236, 238, 244, 255), 10)
    spaced(d, W / 2, BOT_Y0 + PANEL_H + 14, "OVERTHINKER", font("Inter-SemiBold.otf", 40), (200, 204, 214, 255), 10)
    spaced(d, W / 2, TOP_Y0 + PANEL_H + 18, "SAME GAP", font("Inter-SemiBold.otf", 36), (206, 210, 220, 255), 9)
    fm = font(MONO, 50)
    for t0, s, y, col in ((T_L1, LINE1, 56, (250, 250, 252)), (T_L2, LINE2, 122, G.GOLD)):
        if t < t0:
            continue
        k = int(clamp((t - t0) * G.CPS, 0, len(s)))
        full = sum(fm.getlength(c) for c in s) + 3 * (len(s) - 1)
        xx = W / 2 - full / 2
        for c in s[:k]:
            d.text((xx, y), c, font=fm, fill=col + (255,))
            xx += fm.getlength(c) + 3
        if (k < len(s) or (s == LINE2 and t < t0 + len(s) / G.CPS + 1.0)) and int(t * 3.4) % 2 == 0:
            d.rectangle([xx + 2, y + 6, xx + 26, y + 56], fill=col + (220,))
    return np.asarray(img.convert("RGB"))


FRAME0 = None


def init_worker():
    G.BG = G.build_bg()


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
    G.BUB_OT = [(b0, b1, s) for b0, b1, s in BUB_OT + BUB_DOER]
    G.LINE1, G.LINE2 = LINE1, LINE2
    return G.audio()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "one-more-try.mp4"
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
    G.write_wav(wav, audio())
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
