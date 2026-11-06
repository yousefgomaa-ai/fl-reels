# "Strings" (FB Legends, owner 2026-11-06: Ronaldo's farewell, «صوت البيانو متغيرش»): no plucked or struck sound at all,
# so nothing can be heard as a piano: a solo cello sings the tune over a string section and a soft choir («ah»), with a
# low drum only where the story rises (Euro 2016) and at the end. Bowed and sung tones are additive (sines), so the mix
# holds no noise. Synthesised from scratch, no samples, so no third-party rights. python3 strings.py out.wav [bpm]
# Encode: ffmpeg -i out.wav -af lowpass=f=6000,loudnorm=I=-16:TP=-1.5:LRA=11 -c:a libmp3lame -b:a 160k fl-strings.mp3
import numpy as np, wave, sys
from scipy.signal import lfilter
SR = 44100
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, a): return lfilter([a], [1, a - 1], x)
def adsr(n, a, r):
    t = np.arange(n) / SR; T = n / SR
    return np.minimum(1, t / a) * np.clip((T - t) / r, 0, 1)
def bowed(m, n, bright=14, vib=0.004, a=0.35, r=0.6, formant=None):
    """A bowed string: harmonics 1..bright at 1/k with a slow vibrato, shaped by a body resonance."""
    t = np.arange(n) / SR; f = midi(m)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.6))) / SR
    x = sum(np.sin(k * ph) / k * (1 if formant is None else formant(k * f)) for k in range(1, bright + 1) if k * f < 6000)
    return x * adsr(n, a, r)
def cello_body(fr): return 1.0 / (1 + ((fr - 420) / 380) ** 2) + 0.5 / (1 + ((fr - 1100) / 500) ** 2) + 0.15
def choir(m, n):  # «ah»: harmonics weighted by the vowel's formants (700, 1220 Hz), several voices slightly apart
    out = np.zeros(n); t = np.arange(n) / SR
    for d in (-0.006, -0.002, 0.003, 0.007):
        f = midi(m) * (1 + d); ph = 2 * np.pi * np.cumsum(f * (1 + 0.003 * np.sin(2 * np.pi * (4.6 + d * 80) * t))) / SR
        out += sum(np.sin(k * ph) * (1 / (1 + ((k * f - 700) / 160) ** 2) + 0.6 / (1 + ((k * f - 1220) / 200) ** 2)) for k in range(1, 14) if k * f < 5000)
    return out / 4 * adsr(n, 1.6, 1.4)
def drum(n):  # a deep, soft drum: a falling sine, no noise
    t = np.arange(n) / SR; f = 48 + 40 * np.exp(-t * 7)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2) * adsr(n, 0.004, 0.3)
def reverb(x, wet=0.4):
    out = np.zeros_like(x)
    for d, g in ((1931, 0.86), (2111, 0.85), (1777, 0.84), (2297, 0.83)):
        out += lfilter([1], np.r_[1, np.zeros(d - 1), -g], x)
    for d in (225, 341, 441):
        out = lfilter(np.r_[-0.6, np.zeros(d - 1), 1], np.r_[1, np.zeros(d - 1), -0.6], out)
    return x + wet * lp(out, 0.2) / 4
bpm = float(sys.argv[2]) if len(sys.argv) > 2 else 56
beat = 60 / bpm; bar = 4 * beat; bars = 19
N = int(bars * bar * SR) + 5 * SR
L = np.zeros(N); R = np.zeros(N)
def at(t): return int(t * SR)
def put(buf, sig, t, g=1.0):
    i = at(t); j = min(N, i + len(sig)); buf[i:j] += sig[: j - i] * g
# D minor: Dm - Bb - F - C, the lift Gm - Bb - F - A, the close Bb - C - Dm - Dm (the last bar = the first: the loop).
prog = [[38, 50, 53, 57], [34, 46, 50, 53], [41, 48, 53, 57], [36, 48, 52, 55]]
lift = [[43, 50, 55, 58], [34, 46, 50, 53], [41, 48, 53, 57], [33, 49, 52, 57]]
close = [[34, 46, 50, 53], [36, 48, 52, 55], [38, 50, 53, 57], [38, 50, 53, 57]]
# the cello's tune: (note, beats); None = rest
tune = [[(62, 2), (64, 1), (65, 1)], [(65, 2), (62, 2)], [(60, 3), (57, 1)], [(64, 4)],
        [(62, 2), (65, 1), (69, 1)], [(70, 2), (69, 1), (67, 1)], [(65, 3), (64, 1)], [(61, 4)]]
for b in range(bars):
    t0 = b * bar
    c = close[b - 15] if b >= 15 else (lift if 7 <= b < 11 else prog)[b % 4]
    full = 3 <= b < 15
    # the section: low strings on the root, violas and violins on the chord, swelling in from bar 1
    if b >= 0:
        s = sum(bowed(m + 12, at(bar + 1.2), 10, 0.003, 0.9, 1.0) for m in c[1:]) / 3
        put(L, s, t0, 0.32 if b else 0.22); put(R, s, t0 + 0.02, 0.32 if b else 0.22)
        bs = bowed(c[0], at(bar + 1.2), 12, 0.002, 0.8, 1.0, cello_body); put(L, bs, t0, 0.3); put(R, bs, t0, 0.3)
    # the choir from bar 3, louder in the lift
    if full or b in (15, 16):
        ch = sum(choir(m + 12, at(bar + 1.6)) for m in c[1:3]) / 2
        g = 0.2 if 7 <= b < 11 else 0.13
        put(L, ch, t0, g); put(R, ch, t0 + 0.03, g)
    # the cello's tune from bar 1 to bar 16
    if 1 <= b < 17:
        tb = 0
        for m, n in tune[(b - 1) % 8]:
            if m is not None:
                note = bowed(m - 12, at(n * beat + 0.5), 16, 0.005, 0.25, 0.5, cello_body)
                put(L, note, t0 + tb * beat, 0.34); put(R, note, t0 + tb * beat + 0.01, 0.3)
            tb += n
    # the drum: where the story rises (bars 7-10) and the last chord
    if 7 <= b < 11:
        put(L, drum(at(2)), t0, 0.5); put(R, drum(at(2)), t0, 0.5)
        put(L, drum(at(2)), t0 + 2 * beat, 0.32); put(R, drum(at(2)), t0 + 2 * beat, 0.32)
    if b == 16: put(L, drum(at(3)), t0, 0.55); put(R, drum(at(3)), t0, 0.55)
L = reverb(L, 0.55); R = reverb(R, 0.55)
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.05) / np.tanh(1.05); mix /= np.abs(mix).max() * 1.05
f = at(2); mix[:f] *= np.linspace(0, 1, f)[:, None] ** 0.8
f = at(3.5); mix[-f:] *= np.linspace(1, 0, f)[:, None]
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print('seconds', round(N / SR, 1))
