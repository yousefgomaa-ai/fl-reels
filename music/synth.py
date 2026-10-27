# Made for FOOTBALL LEGENDS: python3 synth.py <dir> writes the WAVs. Upbeat but laid-back backing tracks (chill / tropical
# house): warm keys, soft punchy drums, a plucked hook. Synthesised from scratch (no samples), so no third-party rights.
# Encode: ffmpeg -i X.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a libmp3lame -b:a 160k X.mp3
import numpy as np, wave, sys
from scipy.signal import lfilter
SR = 44100
rng = np.random.default_rng(1)

def midi(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, a): return lfilter([a], [1, a - 1], x)
def hp(x, a): return x - lp(x, a)
def env(n, a, d, s=0.0, r=0.01):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * (s + (1 - s) * np.exp(-t / d))
    return e * np.clip((n / SR - t) / r, 0, 1)
def kick(n):
    t = np.arange(n) / SR
    f = 48 + 95 * np.exp(-t * 38)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.16)
    click = hp(rng.standard_normal(n), 0.5) * env(n, 0.0003, 0.003) * 0.25
    return np.tanh((body + click) * 1.6)
def clap(n):
    x = hp(rng.standard_normal(n), 0.2)
    e = sum(env(n, 0.0005, 0.01) * (np.arange(n) >= int(k * SR)) for k in (0, 0.009, 0.019)) * 0.5 + env(n, 0.002, 0.12)
    return lp(x * e, 0.55) * 0.7
def hat(n, d=0.025):
    return hp(rng.standard_normal(n), 0.75) * env(n, 0.0004, d) * 0.3
def shaker(n):
    return hp(rng.standard_normal(n), 0.6) * env(n, 0.012, 0.03) * 0.18
def keys(m, n):  # electric-piano-ish: a few decaying sine partials, a little tremolo
    t = np.arange(n) / SR; f = midi(m)
    x = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3) + 0.12 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 6))
    return x * env(n, 0.004, 1.4, 0.25, 0.08) * (1 + 0.12 * np.sin(2 * np.pi * 4.5 * t))
def pad(ms, n):
    t = np.arange(n) / SR
    x = sum(2 * ((t * midi(m) * (1 + d) + rng.random()) % 1) - 1 for m in ms for d in (-0.005, 0, 0.006))
    return lp(x / (3 * len(ms)), 0.035) * env(n, 0.25, 9, 0.9, 0.2)
def pluck(m, n):  # marimba/steel-ish hook
    t = np.arange(n) / SR; f = midi(m)
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 40) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 12)
    return x * env(n, 0.001, 0.18)
def sub(m, n):
    t = np.arange(n) / SR
    return np.tanh(1.3 * np.sin(2 * np.pi * midi(m) * t)) * env(n, 0.004, 0.5, 0.6, 0.03)
def reverb(x, wet=0.25):
    out = np.zeros_like(x)
    for d, g in ((1557, 0.80), (1617, 0.79), (1491, 0.78), (1422, 0.77)):
        out += lfilter([1], np.r_[1, np.zeros(d - 1), -g], x)
    for d in (225, 556):
        out = lfilter(np.r_[-0.5, np.zeros(d - 1), 1], np.r_[1, np.zeros(d - 1), -0.5], out)
    return x + wet * lp(out, 0.4) / 4

def track(bpm, chords, bass, hook, seed, swing=0.08, bars=24):
    global rng; rng = np.random.default_rng(seed)
    beat = 60 / bpm; bar = 4 * beat; N = int(bars * bar * SR) + 3 * SR
    drums = np.zeros(N); music = np.zeros((N, 2)); duck = np.ones(N)
    def at(t): return int(t * SR)
    def put(buf, sig, t, g=1.0, pan=0.0):
        i = at(t); j = min(N, i + len(sig)); s = sig[: j - i] * g
        if buf.ndim == 1: buf[i:j] += s
        else: buf[i:j, 0] += s * (1 - pan); buf[i:j, 1] += s * (1 + pan)
    for b in range(bars):
        c = chords[b % len(chords)]
        intro = b < 1; brk = b in (14, 15); drop = 2 <= b < 14 or b >= 16
        t0 = b * bar
        # drums: four on the floor from bar 1 (soft in the break), clap on 2 and 4, swung 16th hats, offbeat open hat
        for q in range(4):
            tq = t0 + q * beat
            if not intro and not brk:
                put(drums, kick(at(0.35)), tq, 0.95)
                k = at(tq); L = at(0.22); duck[k:k + L] = np.minimum(duck[k:k + L], 0.45 + 0.55 * np.linspace(0, 1, L) ** 0.6)
            if q in (1, 3) and not intro: put(drums, clap(at(0.35)), tq, 0.5 if brk else 0.62)
            for s in range(4):
                sw = swing * beat if s % 2 else 0
                if drop or s == 2: put(drums, hat(at(0.06)), tq + s * beat / 4 + sw, 0.75 if s == 2 else 0.4)
            if drop: put(drums, shaker(at(0.08)), tq + beat / 2, 0.8)
        # keys: chord stabs on a syncopated rhythm (1, 1&-a, 2&, 3&, 4)
        stabs = [0, 0.75, 1.5, 2.5, 3.5] if not intro else [0]
        for s in stabs:
            L = at(beat * (0.9 if s else 1.6)) if not intro else at(bar)
            for i, m in enumerate(c):
                put(music, keys(m, L), t0 + s * beat, 0.11, (-0.25, 0.1, 0.3, -0.1)[i % 4])
        put(music, pad(c, at(bar)), t0, 0.5 if not brk else 0.7, 0.0)
        # sub bass, tropical rhythm
        if not intro:
            root = bass[b % len(bass)]
            for s, d in ((0, 0.7), (0.75, 0.5), (1.5, 0.45), (2.5, 0.7), (3.25, 0.5)) if drop else ((0, 1.8), (2, 1.8)):
                put(music, sub(root, at(d * beat)), t0 + s * beat, 0.5)
        # hook: the pluck melody over the drops (one bar of 8ths, per chord)
        if drop and b >= 2:
            line = hook[b % len(hook)]
            for s, m in enumerate(line):
                if m is None: continue
                put(music, pluck(m, at(beat * 0.6)), t0 + s * beat / 2 + (swing * beat / 2 if s % 2 else 0), 0.2, 0.3 if s % 2 else -0.3)
        if b == 15:  # rising noise into the second drop
            L = at(bar); x = hp(rng.standard_normal(L), 0.3) * np.linspace(0, 1, L) ** 2.5
            put(drums, x, t0, 0.25)
    music *= duck[:, None]
    music[:, 0] = reverb(music[:, 0], 0.35); music[:, 1] = reverb(music[:, 1][::-1], 0.0)[::-1] * 0 + reverb(music[:, 1], 0.35)
    drums = reverb(drums, 0.12)
    mix = music + drums[:, None] * 0.9
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix /= np.abs(mix).max() * 1.1
    f = at(1.5); mix[:f] *= np.linspace(0.3, 1, f)[:, None] ** 0.5
    f = at(2.5); mix[-f:] *= np.linspace(1, 0, f)[:, None]
    return mix

def save(name, mix):
    with wave.open(name, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())

d = sys.argv[1]
_ = None
# 1 "Golden hour", C major, 112 BPM: F - G - Em - Am (IV V iii vi), uplifting.
save(f'{d}/fl-golden.wav', track(112,
  [[65, 69, 72, 76], [67, 71, 74, 77], [64, 67, 71, 74], [69, 72, 76, 79]], [41, 43, 40, 45],
  [[84, _, 81, 79, 81, _, 76, _], [79, _, 81, 83, 86, _, 83, _], [83, _, 79, 76, 79, _, 74, 76], [76, _, 79, 81, 84, 81, 79, _]], seed=11))
# 2 "Warm-up", D major, 116 BPM: Bm - G - D - A (vi IV I V).
save(f'{d}/fl-warmup.wav', track(116,
  [[59, 62, 66, 69], [55, 59, 62, 66], [62, 66, 69, 73], [57, 61, 64, 69]], [35, 31, 38, 33],
  [[78, _, 74, 78, 81, _, 78, 74], [79, _, 78, 74, 71, _, 74, _], [74, 78, 81, _, 85, _, 81, 78], [76, _, 73, 76, 81, _, _, 76]], seed=12, swing=0.1))
# 3 "Easy win", Eb major, 104 BPM, smoother: Ebmaj7 - Dm7 - Cm7 - Bb6.
save(f'{d}/fl-easywin.wav', track(104,
  [[63, 67, 70, 74], [62, 65, 69, 72], [60, 63, 67, 70], [58, 62, 65, 67]], [39, 38, 36, 34],
  [[82, _, 79, _, 75, 77, 79, _], [81, _, 77, 74, _, 72, 74, _], [79, _, 75, 72, 75, _, 79, 82], [77, _, 74, _, 70, 72, 74, _]], seed=13, swing=0.12))
