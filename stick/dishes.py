#!/usr/bin/env python3
"""WILL IT FALL? - LATER vs NOW, the same sink. 17 s, perfect loop. The 3D panels come from Blender (dishes_bl.py);
this script lays them out with the labels, the DAY counter and the closing lines, scores the music on real
instruments (General MIDI through FluidSynth) and mixes the sound effects.

    blender -b --python stick/dishes_bl.py -- later RENDER/later all
    blender -b --python stick/dishes_bl.py -- now RENDER/now all
    python3 stick/dishes.py RENDER stick/dishes.mp4
"""
import math
import os
import subprocess
import sys

import mido
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
from perfect_wave import env, mix_in, noise, tone, write_wav  # noqa

W, H, FPS, SR = 1080, 1920, 30, 44100
DUR = 17.0
NF = int(DUR * FPS)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
for cand in ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    if os.path.exists(cand):
        BOLD = cand
        break
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

DAYLEN, DAY0, NDAYS = 0.92, -0.25, 14
T_FALL = DAY0 + 13 * DAYLEN + 0.95
T_DUCK = T_FALL - 0.1
T_SWEEP0, T_SWEEP1 = 15.55, 16.25
T_RESTART = DUR + DAY0
T_L1, T_L2 = T_FALL + 0.7, T_FALL + 1.5
T_TITLE_BACK = 16.2
LINE1, LINE2 = "SMALL NOW.", "OR ALL AT ONCE."
GOLD = (255, 200, 70)
WHITE = (245, 245, 245)
GREY = (150, 150, 155)

P_W, P_H = 1040, 760
PX = 20
Y_TITLE = 0
Y_L1 = 214
Y_P1 = 252
Y_MID = Y_P1 + P_H
Y_P2 = Y_MID + 72
Y_L2 = Y_P2 + P_H + 4


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def day_of(t):
    if t >= T_RESTART:
        return 1
    if t >= T_FALL:
        return NDAYS
    return max(1, min(NDAYS, int((t - DAY0) // DAYLEN) + 1))


def release_times():
    out = [DAY0 + (d - 1) * DAYLEN + 0.38 * DAYLEN for d in range(1, NDAYS + 1)]
    return out


def font(sz):
    return ImageFont.truetype(BOLD, int(sz))


def spaced(d, cx, y, s, f, fill, sp=4):
    tw = sum(f.getlength(c) for c in s) + sp * (len(s) - 1)
    x = cx - tw / 2
    for c in s:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + sp


def frame(t, rdir):
    i = int(round(t * FPS)) % NF
    img = Image.new("RGB", (W, H), (0, 0, 0))
    for side, y in (("later", Y_P1), ("now", Y_P2)):
        p = os.path.join(rdir, side, f"{i:04d}.png")
        if os.path.exists(p):
            img.paste(Image.open(p).convert("RGB"), (PX, y))
    d = ImageDraw.Draw(img)
    # title / closing lines
    if T_L1 <= t < T_TITLE_BACK:
        a = 1.0 - clamp((t - (T_TITLE_BACK - 0.3)) / 0.3)
        for t0, s, y, c, sz in ((T_L1, LINE1, 34, WHITE, 76), (T_L2, LINE2, 120, GOLD, 76)):
            if t >= t0:
                k = int(clamp((t - t0) * 18, 0, len(s)))
                col = tuple(int(v * a) for v in c)
                spaced(d, W / 2, y, s[:k], font(sz), col, 5)
    else:
        a = clamp((t - T_TITLE_BACK) / 0.3) if t >= T_TITLE_BACK else 1.0
        if T_FALL <= t < T_L1:
            a = 1.0 - clamp((t - T_FALL) / 0.3)
        col = tuple(int(v * a) for v in WHITE)
        spaced(d, W / 2, 56, "WILL IT FALL?", font(96), col, 6)
    # labels and the counter, like a stage programme
    spaced(d, W / 2, Y_L1, "LATER", font(30), GREY, 8)
    spaced(d, W / 2, Y_L2, "NOW", font(30), GREY, 8)
    spaced(d, W / 2, Y_MID + 6, "SAME SINK", font(22), GREY, 6)
    dd = day_of(t)
    pulse = 0
    for rt in release_times():
        if rt <= t < rt + 0.18:
            pulse = 1 - (t - rt) / 0.18
    spaced(d, W / 2, Y_MID + 30, f"DAY {dd}", font(36 + 6 * pulse), GOLD if dd >= 12 else WHITE, 5)
    arr = np.asarray(img).astype(np.float32)
    if T_FALL <= t < T_FALL + 0.12:
        arr = np.clip(arr + 45 * (1 - (t - T_FALL) / 0.12), 0, 255)
    return arr.astype(np.uint8)


# ---------------------------------------------------------------- music on real instruments
def midi_score(path):
    notes = []          # (start s, dur s, channel, note, velocity)
    programs = {0: 0, 1: 45, 2: 33, 3: 48, 4: 9, 5: 8, 6: 47}   # piano, pizz, bass, strings, glock, celesta, timpani
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]       # Am F C G
    eighth = DAYLEN / 2

    def groove(t0, t1, day_of_bar):
        k = 0
        t = t0
        while t < t1 - 1e-6:
            d = day_of_bar(t)
            ch = chords[(int((t - DAY0) // (2 * DAYLEN))) % 4]
            inten = clamp((d - 1) / 13)
            vel = int(55 + 45 * inten)
            notes.append((t, eighth * 0.9, 0, ch[[0, 2, 1, 2][k % 4]] + 12, vel))
            if k % 2 == 0:
                notes.append((t, eighth * 1.8, 2, ch[0] - 12, 70 + int(25 * inten)))
            if d >= 5:
                notes.append((t, eighth * 0.5, 1, ch[k % 3] + 24, 50 + int(40 * inten)))
            if d >= 9 and k % 4 == 0:
                for n in ch:
                    notes.append((t, 4 * eighth, 3, n + 12, 40 + int(40 * inten)))
            if k % 2 == 0:
                notes.append((t, 0.1, 9, 36, 60 + int(40 * inten)))      # kick
            else:
                notes.append((t, 0.1, 9, 42, 40 + int(30 * inten)))      # hat
            if d >= 12:
                notes.append((t, eighth, 6, 45, 70 + int(40 * inten)))   # timpani roll-ish
            k += 1
            t += eighth

    groove(0.0, T_FALL - 0.05, day_of)
    # the loop: the day-1 groove comes back from T_RESTART
    groove(T_RESTART, DUR, lambda t: 1)
    # clinks on every placement: glockenspiel climbing with the tower
    for d, rt in enumerate(release_times(), 1):
        notes.append((rt, 0.4, 4, 72 + d, 80))
        notes.append((rt + 0.08, 0.4, 4, 76 + d, 70))
        notes.append((rt + 0.25 * DAYLEN, 0.5, 5, 84 + (d % 5), 60))       # NOW's sparkle in the rack
    # after the crash: a warm chord under the closing lines
    for n in (45, 57, 60, 64, 69):
        notes.append((T_L1 - 0.2, 2.6, 3, n, 70))
    for j, n in enumerate((76, 72, 69, 67)):
        notes.append((T_L1 + j * 0.4, 0.8, 0, n, 70))
    # write it
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    for ch, pg in programs.items():
        tr.append(mido.Message("program_change", channel=ch, program=pg, time=0))
        tr.append(mido.Message("control_change", channel=ch, control=91, value=60, time=0))
    tr.append(mido.Message("control_change", channel=4, control=7, value=110, time=0))
    tr.append(mido.Message("control_change", channel=6, control=7, value=80, time=0))
    ev = []
    for s, du, ch, n, v in notes:
        ev.append((s, 1, ch, n, v))
        ev.append((s + du, 0, ch, n, 0))
    ev.sort(key=lambda e: (e[0], e[1]))
    now = 0
    for s, on, ch, n, v in ev:
        tk = int(round(max(0.0, s) * 960))
        tr.append(mido.Message("note_on" if on else "note_off", channel=ch, note=int(n), velocity=int(v),
                               time=max(0, tk - now)))
        now = max(now, tk)
    mid.save(path)


def audio(tmp):
    n = int(DUR * SR)
    mp = os.path.join(tmp, "score.mid")
    wp = os.path.join(tmp, "score.wav")
    midi_score(mp)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.7", "-r", str(SR), "-F", wp, SF2, mp], check=True,
                   capture_output=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wp, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    mus = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    x = np.zeros((n, 2))
    x[:min(n, len(mus))] += mus[:n]
    fx = np.zeros((n, 2))
    # water while NOW washes (first ~45% of each day)
    for d in range(1, NDAYS + 1):
        t0 = DAY0 + (d - 1) * DAYLEN
        if 0 <= t0 < T_FALL:
            mix_in(fx, noise(0.4, 100 + d, lo=900, hi=7000) * np.sin(np.linspace(0, np.pi, int(0.4 * SR))), t0,
                   0.03, 0.3)
    # the crash: a ceramic avalanche + thud
    mix_in(fx, tone(55, 1.2, (1, 0.6, 0.3), a=0.002, d=0.5, sweep=35), T_FALL + 0.25, 0.45)
    rng = np.random.default_rng(5)
    for j in range(60):
        at = T_FALL + 0.2 + rng.uniform(0, 1.1) ** 1.6
        f = rng.uniform(2200, 6500)
        mix_in(fx, tone(f, 0.18, (1, 0.5), a=0.0005, d=0.05), at, 0.05, rng.uniform(-0.8, 0.8))
        mix_in(fx, noise(0.12, 300 + j, lo=2500, hi=11000) * env(int(0.12 * SR), 0.0005, 0.03), at, 0.08,
               rng.uniform(-0.8, 0.8))
    mix_in(fx, noise(1.5, 9, lo=200, hi=8000) * env(int(1.5 * SR), 0.003, 0.5), T_FALL + 0.2, 0.18)
    # the creak before it goes
    mix_in(fx, tone(140, 0.9, (1, 0.6, 0.4, 0.3), a=0.2, d=0.5, sweep=95), T_FALL - 0.7, 0.07)
    # the sweep into the bin
    mix_in(fx, noise(0.7, 11, lo=300, hi=5000) * np.sin(np.linspace(0, np.pi, int(0.7 * SR))), T_SWEEP0, 0.12)
    for j in range(5):
        mix_in(fx, tone(2800 + 300 * j, 0.1, (1,), a=0.001, d=0.04), T_SWEEP1 - 0.25 + j * 0.04, 0.03)
    for t0 in (T_L1, T_L2):
        for i2 in range(12):
            mix_in(fx, noise(0.03, 500 + i2 + int(t0 * 10), lo=1200, hi=4000) * env(int(0.03 * SR), 0.001, 0.008),
                   t0 + i2 / 18, 0.04)
    x += fx
    m = int(0.3 * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    rdir, out = sys.argv[1], sys.argv[2]
    tmp = os.path.join(rdir, "tmp")
    os.makedirs(tmp, exist_ok=True)
    only = os.environ.get("ONLY_FRAMES")
    if only:
        for s in only.split(","):
            Image.fromarray(frame(float(s), rdir)).save(os.path.join(tmp, f"c{float(s):05.2f}.png"))
        return
    wav = os.path.join(tmp, "mix.wav")
    write_wav(wav, audio(tmp))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "hqdn3d=2:1.5:3:3", "-c:v", "libx264",
                          "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                          "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "192k",
                          "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(NF):
        p.stdin.write(frame(i / FPS, rdir).tobytes())
    p.stdin.close()
    p.wait()
    print(out)


if __name__ == "__main__":
    main()
