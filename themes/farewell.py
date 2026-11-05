# "Farewell" (FB Legends, owner 2026-11-05: a farewell reel, «موسيقى غير المعتادة»): slow felt piano, a music-box line,
# a heartbeat instead of drums, strings that swell and fall back; it ends where it began, so a looping reel does not
# jump. Synthesised from scratch, no samples, so no third-party rights. python3 farewell.py out.wav [bpm] [seed]
# Encode: ffmpeg -i out.wav -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a libmp3lame -b:a 160k fl-farewell.mp3
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


def felt(m, n):  # a soft, muffled piano: fewer partials, a slower hammer
    t = np.arange(n) / SR; f = midi(m)
    x = sum(a * np.sin(2 * np.pi * k * f * t * (1 + 0.0003 * k)) * np.exp(-t * (0.9 + k * 1.4)) for k, a in ((1, 1), (2, 0.3), (3, 0.08)))
    return lp(x * env(n, 0.012, 4, 0.0, 0.3), 0.35)
def bell(m, n):  # a music box: bright, short, a little detuned
    t = np.arange(n) / SR; f = midi(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 4.02 * t) * np.exp(-t * 9) + 0.2 * np.sin(2 * np.pi * f * 2.99 * t) * np.exp(-t * 5)
    return x * env(n, 0.002, 1.1, 0.0, 0.2)
def heart(n):  # lub-dub, low and soft
    t = np.arange(n) / SR; f = 46 + 30 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.004, 0.11)
bpm = float(sys.argv[2]) if len(sys.argv) > 2 else 64
beat = 60 / bpm; bar = 4 * beat; bars = 20
N = int(bars * bar * SR) + 3 * SR
L = np.zeros(N); R = np.zeros(N); D = np.zeros(N)
def at(t): return int(t * SR)
def put(buf, sig, t, g=1.0):
    i = at(t); j = min(N, i + len(sig)); buf[i:j] += sig[: j - i] * g
# A minor, bittersweet: Am - F - C - G, then F - G - Am - Am for the close; the last bar is the first again (the loop).
prog = [[45, 52, 57, 60], [41, 48, 53, 57], [48, 55, 60, 64], [43, 50, 55, 59]]
close = [[41, 48, 53, 57], [43, 50, 55, 59], [45, 52, 57, 60], [45, 52, 57, 64]]
mel = [[76, None, 72, 71], [72, None, 69, None], [67, 72, 74, 76], [74, None, 71, None]]
for b in range(bars):
    t0 = b * bar; c = (close if b >= 16 else prog)[b % 4]
    strong = 4 <= b < 16
    # felt piano: the chord broken slowly, two notes a beat
    for k, m in enumerate([c[0], c[2] + 12, c[1] + 12, c[3] + 12, c[2] + 12, c[3] + 12, c[1] + 12, c[2] + 12]):
        put(L if k % 2 else R, felt(m, at(beat * 2.2)), t0 + k * beat / 2, 0.2); put(R if k % 2 else L, felt(m, at(beat * 2.2)), t0 + k * beat / 2 + 0.015, 0.09)
    put(L, felt(c[0] - 12, at(bar * 1.2)), t0, 0.28); put(R, felt(c[0] - 12, at(bar * 1.2)), t0, 0.28)
    # strings from bar 2, fuller in the middle, gone in the last two bars (back to the bare start)
    if 2 <= b < 18:
        s = strings([m + 12 for m in c[1:]] + [c[0]], at(bar + 0.8)); g = 0.5 if strong else 0.32
        put(L, s, t0, g); put(R, s, t0 + 0.015, g)
    # the music box from bar 4, one bar in two near the end
    if 4 <= b < 18 and not (b >= 14 and b % 2):
        for k, m in enumerate(mel[b % 4]):
            if m: put(L, bell(m + 12, at(beat * 2)), t0 + k * beat, 0.09); put(R, bell(m + 12, at(beat * 2)), t0 + k * beat + 0.02, 0.07)
    # a heartbeat on beats 1 and 3, from bar 2 to bar 17
    if 2 <= b < 18:
        for q in (0, 2):
            put(D, heart(at(0.25)), t0 + q * beat, 0.5 if strong else 0.32); put(D, heart(at(0.25)), t0 + q * beat + 0.22, 0.32 if strong else 0.2)
    if b in (8, 12): put(D, boom(at(3)), t0, 0.28)
L = reverb(L, 0.75); R = reverb(R, 0.75); D = reverb(D, 0.3)
mix = np.stack([L + D * 0.8, R + D * 0.8], 1)
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix /= np.abs(mix).max() * 1.05
f = at(1.5); mix[:f] *= np.linspace(0, 1, f)[:, None] ** 0.7
f = at(3); mix[-f:] *= np.linspace(1, 0, f)[:, None]
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print('seconds', round(N / SR, 1))
