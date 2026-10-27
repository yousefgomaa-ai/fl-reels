# "Legends" (FOOTBALL LEGENDS): the coach series' theme, calm but stirring (piano arpeggio, warm strings, soft pulse,
# low toms). Synthesised from scratch, no samples, so no third-party rights. python3 legends.py out.wav [bpm] [seed]
# Encode: ffmpeg -i out.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a libmp3lame -b:a 160k fl-legends.mp3
import numpy as np, wave, sys
from scipy.signal import lfilter
SR = 44100
rng = np.random.default_rng(int(sys.argv[3]) if len(sys.argv) > 3 else 7)
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, a): return lfilter([a], [1, a - 1], x)
def hp(x, a): return x - lp(x, a)
def env(n, a, d, s=0.0, r=0.01):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * (s + (1 - s) * np.exp(-t / d))
    return e * np.clip((n / SR - t) / r, 0, 1)
def piano(m, n):
    t = np.arange(n) / SR; f = midi(m)
    x = sum(a * np.sin(2 * np.pi * k * f * t * (1 + 0.0004 * k)) * np.exp(-t * (1.6 + k * 1.1)) for k, a in ((1, 1), (2, 0.45), (3, 0.2), (4, 0.12), (5, 0.05)))
    return x * env(n, 0.003, 3, 0.0, 0.05)
def strings(ms, n):
    t = np.arange(n) / SR
    x = sum(2 * ((t * midi(m) * (1 + d) + rng.random()) % 1) - 1 for m in ms for d in (-0.004, -0.0015, 0.002, 0.005))
    x = lp(lp(x / (4 * len(ms)), 0.05), 0.08)
    vib = 1 + 0.04 * np.sin(2 * np.pi * 0.25 * t)
    return x * vib * env(n, 0.9, 30, 1.0, 0.6)
def tom(n, f0=70):
    t = np.arange(n) / SR; f = f0 + 60 * np.exp(-t * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.35)
    return np.tanh(body * 1.4 + lp(rng.standard_normal(n), 0.1) * env(n, 0.001, 0.05) * 0.3)
def pulse(n):
    t = np.arange(n) / SR; f = 50 + 70 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.12)
def tick(n): return hp(rng.standard_normal(n), 0.8) * env(n, 0.0004, 0.02) * 0.2
def boom(n):
    t = np.arange(n) / SR; f = 38 + 50 * np.exp(-t * 6)
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.005, 1.4) * 1.8) + lp(rng.standard_normal(n), 0.05) * env(n, 0.01, 0.8) * 0.4
def reverb(x, wet=0.3):
    out = np.zeros_like(x)
    for d, g in ((1789, 0.84), (1913, 0.83), (1687, 0.82), (2053, 0.81)):
        out += lfilter([1], np.r_[1, np.zeros(d - 1), -g], x)
    for d in (225, 556, 441):
        out = lfilter(np.r_[-0.6, np.zeros(d - 1), 1], np.r_[1, np.zeros(d - 1), -0.6], out)
    return x + wet * lp(out, 0.3) / 4

bpm = float(sys.argv[2]) if len(sys.argv) > 2 else 96
beat = 60 / bpm; bar = 4 * beat; bars = 11
N = int(bars * bar * SR) + 4 * SR
L = np.zeros(N); R = np.zeros(N); D = np.zeros(N)
def at(t): return int(t * SR)
def put(buf, sig, t, g=1.0):
    i = at(t); j = min(N, i + len(sig)); buf[i:j] += sig[: j - i] * g
# D minor, i - VI - III - VII (Dm Bb F C), then Gm - Bb - F - A for the lift
chords = [[50, 57, 62, 65], [46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64]]
lift = [[43, 50, 55, 58], [46, 53, 58, 62], [53, 57, 60, 65], [45, 52, 57, 61]]
melody = [[74, 77, 76, 74], [74, 72, 70, 69], [69, 72, 77, 76], [76, 74, 72, 76]]
for b in range(bars):
    t0 = b * bar
    c = (lift if 6 <= b < 10 else chords)[b % 4]
    if b == bars - 1: c = [50, 57, 62, 65, 69]
    # strings: always, swelling in
    s = strings([m + 12 for m in c[1:]] + [c[0]], at(bar + 0.6)); put(L, s, t0, 0.55 if b > 0 else 0.42); put(R, s, t0 + 0.012, 0.55 if b > 0 else 0.42)
    if b == bars - 1:
        put(D, boom(at(3.5)), t0, 0.9)
        for k, m in enumerate(c): put(L, piano(m + 12, at(4)), t0 + k * 0.03, 0.2); put(R, piano(m + 12, at(4)), t0 + k * 0.03, 0.2)
        break
    # piano arpeggio in 8ths (from bar 0)
    arp = [c[0] + 12, c[1] + 12, c[2] + 12, c[3] + 12, c[2] + 24, c[3] + 12, c[2] + 12, c[1] + 12]
    for k, m in enumerate(arp):
        p = piano(m, at(beat * 1.6)); g = 0.16 if b < 2 else 0.13
        put(L if k % 2 else R, p, t0 + k * beat / 2, g); put(R if k % 2 else L, p, t0 + k * beat / 2 + 0.01, g * 0.5)
    # bass note
    put(L, piano(c[0] - 12, at(bar)), t0, 0.22); put(R, piano(c[0] - 12, at(bar)), t0, 0.22)
    # soft pulse from bar 2, full drums from bar 4, lighter in bars 8-9, back for the lift end
    if b >= 1:
        for q in range(4): put(D, pulse(at(0.3)), t0 + q * beat, 0.55 if b >= 2 else 0.35)
    if b >= 2:
        for q in range(8): put(D, tick(at(0.05)), t0 + q * beat / 2, 0.6 if q % 2 else 0.3)
        put(D, tom(at(0.6), 82), t0 + 1.5 * beat, 0.45); put(D, tom(at(0.6), 66), t0 + 3 * beat, 0.5); put(D, tom(at(0.6), 60), t0 + 3.5 * beat, 0.45)
    if b in (2, 6): put(D, boom(at(2.5)), t0, 0.45)
    # melody (piano octave) from bar 4
    if b >= 2:
        for k, m in enumerate(melody[b % 4]):
            put(L, piano(m, at(beat * 1.8)), t0 + k * beat, 0.2); put(R, piano(m + 12, at(beat * 1.8)), t0 + k * beat + 0.005, 0.07); put(R, piano(m, at(beat * 1.8)), t0 + k * beat, 0.14)
    if b == 9:  # rise into the end
        n = at(bar); x = hp(rng.standard_normal(n), 0.25) * np.linspace(0, 1, n) ** 3; put(D, x, t0, 0.18)
L = reverb(L, 0.5); R = reverb(R, 0.5); D = reverb(D, 0.2)
mix = np.stack([L + D * 0.9, R + D * 0.9], 1)
mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix /= np.abs(mix).max() * 1.05
f = at(1.2); mix[:f] *= np.linspace(0, 1, f)[:, None] ** 0.7
f = at(2.5); mix[-f:] *= np.linspace(1, 0, f)[:, None]
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print('seconds', round(N / SR, 1))
