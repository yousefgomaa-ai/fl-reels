# "Fado" (FB Legends, owner 2026-11-05: Ronaldo's farewell, «غير المزيكا»): a Portuguese guitar in the fado manner,
# plucked strings (Karplus-Strong), the melody played as a tremolo, a soft bass guitar under it, a low bowed drone in
# the second half; no noise at all in the mix (the owner heard a hiss), the attack burst filtered before it rings.
# Synthesised from scratch, no samples, so no third-party rights. python3 fado.py out.wav [bpm]
# Encode: ffmpeg -i out.wav -af lowpass=f=5000,loudnorm=I=-16:TP=-1.5:LRA=11 -c:a libmp3lame -b:a 160k fl-fado.mp3
import numpy as np, wave, sys
from scipy.signal import lfilter
SR = 44100
rng = np.random.default_rng(5)
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, a): return lfilter([a], [1, a - 1], x)
def pluck(m, dur, bright=0.5, decay=0.996):
    """Karplus-Strong string: a short filtered burst through a tuned delay line that loses a little each pass."""
    f = midi(m); p = int(SR / f); n = int(dur * SR)
    buf = lp(rng.uniform(-1, 1, p), bright)  # the pick: a soft burst, low-passed so no hiss rings on
    out = np.zeros(n); b = buf.copy(); i = 0
    for k in range(n):
        out[k] = b[i]; j = (i + 1) % p
        b[i] = decay * 0.5 * (b[i] + b[j]); i = j
    out = lp(lp(out, 0.4), 0.5)  # softer still: no bright pick on the attack (2026-11-05, the owner heard a hiss)
    t = np.arange(n) / SR
    return out * np.clip((dur - t) / 0.08, 0, 1)
def bow(m, n):  # a low bowed drone: sines only, a slow swell
    t = np.arange(n) / SR; f = midi(m)
    x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) + 0.15 * np.sin(2 * np.pi * 3 * f * t)
    e = np.minimum(1, t / 2.5) * np.clip((n / SR - t) / 1.5, 0, 1)
    return x * e * (1 + 0.05 * np.sin(2 * np.pi * 4.5 * t))
def reverb(x, wet=0.35):
    out = np.zeros_like(x)
    for d, g in ((1557, 0.82), (1617, 0.81), (1491, 0.8), (1422, 0.79)):
        out += lfilter([1], np.r_[1, np.zeros(d - 1), -g], x)
    for d in (225, 341, 441):
        out = lfilter(np.r_[-0.6, np.zeros(d - 1), 1], np.r_[1, np.zeros(d - 1), -0.6], out)
    return x + wet * lp(out, 0.25) / 4
bpm = float(sys.argv[2]) if len(sys.argv) > 2 else 62
beat = 60 / bpm; bar = 3 * beat; bars = 30  # a slow 3/4, as fado often is
N = int(bars * bar * SR) + 4 * SR
L = np.zeros(N); R = np.zeros(N)
def at(t): return int(t * SR)
def put(buf, sig, t, g=1.0):
    i = at(t); j = min(N, i + len(sig)); buf[i:j] += sig[: j - i] * g
# A minor: i - iv - V7 - i (Am Dm E7 Am), twice, then F - E7 - Am - Am; the last bars are the first again (the loop).
prog = [[45, 57, 60, 64], [50, 57, 62, 65], [40, 56, 59, 62], [45, 57, 60, 64]]
end = [[41, 57, 60, 65], [40, 56, 59, 62], [45, 57, 60, 64], [45, 57, 60, 64]]
melA = [[76, 74, 72], [74, 77, 76], [71, 74, 76], [72, None, None]]
melB = [[79, 77, 76], [77, 74, 72], [71, 72, 74], [69, None, None]]
for b in range(bars):
    t0 = b * bar; c = (end if b >= 24 else prog)[b % 4]
    mid = 8 <= b < 24
    # bass on 1, the chord picked on 2 and 3 (the fado guitar's accompaniment)
    put(L, pluck(c[0], bar * 1.1, 0.35, 0.997), t0, 0.5); put(R, pluck(c[0], bar * 1.1, 0.35, 0.997), t0 + 0.008, 0.45)
    for q in (1, 2):
        for k, m in enumerate(c[1:]):
            put(L if k % 2 else R, pluck(m, beat * 1.4, 0.45, 0.994), t0 + q * beat + k * 0.012, 0.16)
    # the melody, from bar 4: each note a tremolo (the guitar's trill), the last of each phrase held
    if 4 <= b < 28 and not (b >= 24 and b % 2):
        mel = (melB if (b // 4) % 2 else melA)[b % 4]
        for k, m in enumerate(mel):
            if m is None: continue
            held = k == len(mel) - 1 or mel[k + 1] is None if k + 1 < len(mel) else True
            dur = beat * (3 - k if held else 1)
            reps = int(dur / 0.11)
            for r in range(reps):
                g = 0.2 * (0.75 + 0.25 * np.sin(r * 0.7)) * (1 - 0.5 * r / max(1, reps))
                put(L, pluck(m, 0.35, 0.3, 0.993), t0 + k * beat + r * 0.11, g * 0.8); put(R, pluck(m, 0.35, 0.3, 0.993), t0 + k * beat + r * 0.11 + 0.006, g * 0.9)
    # the drone under the middle
    if mid and b % 2 == 0:
        d = bow(c[0] - 12, at(bar * 2.2)); put(L, d, t0, 0.07); put(R, d, t0, 0.07)
L = reverb(L, 0.5); R = reverb(R, 0.5)
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix /= np.abs(mix).max() * 1.05
f = at(1.2); mix[:f] *= np.linspace(0, 1, f)[:, None] ** 0.7
f = at(3); mix[-f:] *= np.linspace(1, 0, f)[:, None]
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print('seconds', round(N / SR, 1))
