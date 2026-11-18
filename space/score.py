#!/usr/bin/env python3
"""Trailer-style score for the space reel "If the Sun vanished", made from sines only (no samples, no noise).

    python3 space/score.py out/score.wav

Cues follow the six scenes (seconds):
  0.0  Sun        swelling D-minor chord, rising, hard cut to silence at 2.3 (the Sun vanishes)
  2.8  BRAAM      "...you wouldn't know for 8 minutes"
  4.0  light      clock ticks + a low eighth-note ostinato starts
  9.0  gravity    ostinato grows, a high minor-second tremolo creeps in, riser into 14
 14.0  darkness   BRAAM + sub drop, then a low drone
 19.0  drifting   lonely pad and a slow pluck motif
 23.0  Saturn     shimmering arpeggio and a wide major swell, cut at 26.7 (the question stays open)
"""
import math
import sys
import wave

import numpy as np

SR = 44100
DUR = 27.0
N = int(DUR * SR)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def fade_edges(x, a=0.004, r=0.02):
    n = len(x)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        x[:na] *= np.linspace(0, 1, na)
    if nr:
        x[-nr:] *= np.linspace(1, 0, nr)
    return x


def saw(freq, dur, nh=24, bright=None, detune=(0.0,)):
    """Band-limited saw from sines. bright(t) in 0..1 opens the 'filter' over time (harmonic roll-off)."""
    t = t_axis(dur)
    y = np.zeros_like(t)
    for d in detune:
        f = freq * 2 ** (d / 1200)
        for k in range(1, nh + 1):
            if f * k > 9000:
                break
            amp = 1.0 / k
            if bright is not None:
                amp = amp * np.exp(-(k - 1) * (1.0 - bright(t)) * 0.55)
            y += amp * np.sin(2 * np.pi * f * k * t + k * 0.7 + d)
    return y / len(detune)


def env_adsr(dur, a, d, s, r):
    t = t_axis(dur)
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = int(r * SR)
    if rel and rel < len(e):
        e[-rel:] *= np.linspace(1, 0, rel)
    return e


class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2))

    def add(self, sig, at, gain=1.0, pan=0.0):
        i = int(at * SR)
        if i >= N:
            return
        sig = sig[: N - i]
        l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        self.x[i:i + len(sig), 0] += sig * gain * l * 1.41
        self.x[i:i + len(sig), 1] += sig * gain * r * 1.41


def reverb(x, secs=2.6, wet=0.32, seed=3):
    """Deterministic sparse-tap reverb (FFT convolution); on tonal input it gives a smooth tail, not hiss."""
    rng = np.random.default_rng(seed)
    n = int(secs * SR)
    out = np.zeros_like(x)
    for ch in range(2):
        ir = np.zeros(n)
        taps = np.sort(rng.integers(int(0.012 * SR), n, 2600))
        ir[taps] = rng.choice([-1.0, 1.0], len(taps)) * np.exp(-taps / SR * 6.9 / secs)
        ir[0] = 0
        # soften the tail: a short moving average lowers its top end
        k = 24
        ir = np.convolve(ir, np.ones(k) / k, mode="same")
        L = 1 << int(np.ceil(np.log2(len(x) + n)))
        y = np.fft.irfft(np.fft.rfft(x[:, ch], L) * np.fft.rfft(ir, L), L)[: len(x)]
        out[:, ch] = y
    out *= wet / (np.abs(out).max() + 1e-9) * np.abs(x).max()
    return x + out


def braam(bus, at, root=38, gain=1.0, dur=3.6):
    """Trailer horn hit: a detuned brass-like saw stack whose 'filter' opens then closes, with a sub boom."""
    br = lambda t: np.clip(np.minimum(t / 0.12, 1.0) * np.exp(-t / 1.4), 0, 1)
    for n, g in [(root, 1.0), (root + 7, 0.6), (root + 12, 0.7), (root + 15, 0.35), (root + 19, 0.3)]:
        s = saw(midi(n), dur, nh=30, bright=br, detune=(-9, 0, 8))
        bus.add(fade_edges(s * env_adsr(dur, 0.035, 1.6, 0.25, 0.9)), at, gain * g * 0.16, pan=(n % 5 - 2) * 0.15)
    t = t_axis(2.2)
    f = 62 * (34 / 62) ** np.minimum(t / 0.6, 1)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.7)
    bus.add(fade_edges(sub, 0.002, 0.05), at, gain * 0.9)


def build():
    mus, fx = Bus(), Bus()

    # 0 - 2.3: the Sun, a swelling D-minor chord with a rising line, then a hard cut to silence
    sw = 2.3
    for n, g, p in [(50, 1, -0.3), (53, 0.8, 0.3), (57, 0.8, -0.1), (62, 0.6, 0.2), (65, 0.4, -0.2), (69, 0.35, 0.1)]:
        br = lambda t: np.clip(t / sw, 0, 1) ** 1.5
        s = saw(midi(n), sw, nh=16, bright=br, detune=(-7, 6))
        e = (t_axis(sw) / sw) ** 1.8
        mus.add(fade_edges(s * e, 0.01, 0.004), 0.0, 0.11 * g, p)
    t = t_axis(sw)
    f = 300 * (2400 / 300) ** (t / sw)
    rise = sum(np.sin(2 * np.pi * np.cumsum(f * m) / SR) / (i + 1) for i, m in enumerate([1, 1.5, 2.01]))
    mus.add(fade_edges(rise * (t / sw) ** 3, 0.01, 0.004), 0.0, 0.05)
    braam(fx, 0.0, root=26, gain=0.35, dur=2.3)  # a low bed under the opening shot

    # 2.8: first BRAAM with the "8 minutes" line
    braam(fx, 2.8, root=38, gain=1.0)

    # 4 - 9: clock ticks once a second
    for k in range(5):
        tk = t_axis(0.07)
        tick = (np.sin(2 * np.pi * 2300 * tk) * 0.6 + np.sin(2 * np.pi * 1150 * tk)) * np.exp(-tk / 0.012)
        fx.add(fade_edges(tick, 0.0008, 0.005), 4.0 + k, 0.22 if k % 2 == 0 else 0.15, pan=0.3 if k % 2 else -0.3)

    # 4 - 14: low ostinato in eighths (120 bpm), D-D-F-D-A-D-F-E, growing
    pat = [38, 38, 41, 38, 45, 38, 41, 40]
    step = 0.25
    i = 0
    t0 = 4.0
    while t0 + i * step < 14.0:
        at = t0 + i * step
        prog = (at - 4.0) / 10.0
        n = pat[i % len(pat)]
        d = step * 0.9
        br = lambda t, p=prog: np.full_like(t, 0.25 + 0.55 * p)
        s = saw(midi(n), d, nh=18, bright=br, detune=(-5, 5))
        acc = 1.0 if i % 4 == 0 else 0.72
        mus.add(fade_edges(s * env_adsr(d, 0.004, 0.09, 0.35, 0.03)), at, (0.09 + 0.12 * prog) * acc, (-0.25 if i % 2 else 0.25))
        if i % 2 == 0:  # octave below on the beat
            s2 = saw(midi(n - 12), d, nh=10, bright=br)
            mus.add(fade_edges(s2 * env_adsr(d, 0.004, 0.12, 0.3, 0.03)), at, 0.09 + 0.08 * prog)
        i += 1
    # soft pulse-kick on each beat from 6 s
    for b in np.arange(6.0, 14.0, 0.5):
        tk = t_axis(0.3)
        f = 95 * (40 / 95) ** np.minimum(tk / 0.12, 1)
        k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tk / 0.11)
        fx.add(fade_edges(k, 0.002, 0.02), b, 0.35 + 0.25 * (b - 6) / 8)

    # 9 - 14: a high minor-second tremolo creeping in
    dur = 5.0
    t = t_axis(dur)
    trem = 0.5 + 0.5 * np.sin(2 * np.pi * 11 * t)
    for n, p in [(81, -0.5), (82, 0.5)]:
        s = saw(midi(n), dur, nh=6, detune=(-6, 6))
        mus.add(fade_edges(s * trem * (t / dur) ** 2, 0.05, 0.004), 9.0, 0.05, p)
    # riser 12.6 - 14
    rd = 1.4
    t = t_axis(rd)
    f = 180 * (1800 / 180) ** (t / rd) ** 1.6
    r = sum(np.sin(2 * np.pi * np.cumsum(f * m) / SR) / (j + 1) for j, m in enumerate([1, 1.005, 2.0, 3.0]))
    fx.add(fade_edges(r * (t / rd) ** 2.5, 0.01, 0.004), 12.6, 0.12)

    # 14: darkness at noon - second BRAAM, lower and longer, then a drone
    braam(fx, 14.0, root=33, gain=1.15, dur=4.5)
    dd = 5.2
    t = t_axis(dd)
    for n, g in [(26, 1.0), (33, 0.6), (38, 0.4)]:
        s = saw(midi(n), dd, nh=8, detune=(-4, 4)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.35 * t))
        mus.add(fade_edges(s * env_adsr(dd, 0.4, 3, 0.6, 1.2), 0.3, 0.6), 14.2, 0.07 * g)

    # 19 - 23: drifting away, a lonely pad and a slow pluck motif
    pd = 4.4
    for n, p in [(50, -0.4), (57, 0.4), (60, -0.2), (64, 0.2)]:
        s = saw(midi(n), pd, nh=7, detune=(-8, 8))
        mus.add(fade_edges(s * env_adsr(pd, 1.2, 3, 0.8, 1.0)), 19.0, 0.045, p)
    for k, (n, at) in enumerate([(74, 19.2), (77, 19.9), (76, 20.6), (72, 21.3), (69, 22.0)]):
        d = 1.6
        tk = t_axis(d)
        y = sum((0.6 ** j) * np.sin(2 * np.pi * midi(n) * (j + 1) * tk) * np.exp(-tk * (2.2 + j * 1.3)) for j in range(5))
        mus.add(fade_edges(y, 0.003, 0.05), at, 0.13, pan=(-0.3 if k % 2 else 0.3))

    # 23 - 26.7: Saturn - shimmering D-major arpeggio and a wide swell, cut at 26.7
    cut = 26.7
    arp = [62, 66, 69, 73, 76, 73, 69, 66]
    a = 0
    at = 23.0
    while at < cut - 0.05:
        n = arp[a % len(arp)] + 12
        d = 0.5
        tk = t_axis(d)
        y = (np.sin(2 * np.pi * midi(n) * tk) + 0.3 * np.sin(4 * np.pi * midi(n) * tk)) * np.exp(-tk / 0.35)
        mus.add(fade_edges(y, 0.003, 0.02), at, 0.05 + 0.04 * (at - 23) / 3.7, pan=math.sin(a * 0.9) * 0.6)
        a += 1
        at += 0.125
    sd = cut - 23.0
    t = t_axis(sd)
    for n, p in [(50, -0.3), (57, 0.3), (62, -0.15), (66, 0.15), (69, 0.0), (74, 0.25)]:
        br = lambda t: np.clip(t / sd, 0, 1)
        s = saw(midi(n), sd, nh=14, bright=br, detune=(-7, 7))
        mus.add(fade_edges(s * (t / sd) ** 2, 0.05, 0.004), 23.0, 0.085, p)
    braam(fx, 23.0, root=38, gain=0.45, dur=3.7)

    x = mus.x + fx.x
    # hard cuts: the Sun vanishing and the open ending
    tt = np.arange(N) / SR
    gate = np.ones(N)
    gate[(tt >= 2.3) & (tt < 2.8)] = 0.0
    gate[tt >= cut] = 0.0
    x = x * gate[:, None]
    x = reverb(x)
    x = x * np.clip((DUR - tt) / 0.05, 0, 1)[:, None]  # the reverb tail fades by the very end
    x -= x.mean(axis=0)
    x = np.tanh(x / (np.abs(x).max() + 1e-9) * 1.6)
    x *= 0.89 / np.abs(x).max()
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "space/score.wav"
    x = build()
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", out)


if __name__ == "__main__":
    main()
