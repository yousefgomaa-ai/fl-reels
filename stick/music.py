#!/usr/bin/env python3
"""A small library of calm backing tracks, so every reel gets its own music.

All of them follow the channel's shape: soft from the first frame, a slow crescendo to the twist (t_end), silence,
a warm chord under the closing line (t_warm) and a few soft notes as the caption types (t_line).

    mus = music.score("guitar_g", DUR, t_end=12.0)
"""
import numpy as np

import perfect_wave as PW
import game_spend as GS
import one_call as OC
from perfect_wave import SR, midi, mix_in, noise, prog

# ---------------------------------------------------------------- instruments
def piano(f, dur=1.4):
    return OC.piano(f, dur, 0.5)


def music_box(f, dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 9)
    x += 0.15 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 16)
    return x * np.minimum(1, t / 0.002) * np.exp(-t * 2.4)


def kalimba(f, dur=1.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 5.95 * t) * np.exp(-t * 20)
    return x * np.minimum(1, t / 0.003) * np.exp(-t * 3.2)


def marimba(f, dur=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 30)
    return x * np.minimum(1, t / 0.002) * np.exp(-t * 5.5)


def pluck(f, dur=1.6, bright=0.5, seed=0):
    """Karplus-Strong string."""
    n = int(dur * SR)
    p = max(2, int(SR / f))
    rng = np.random.default_rng(int(f * 10) + seed)
    buf = PW.filt(rng.uniform(-1, 1, p * 4), hi=2000 + 6000 * bright)[:p]
    out = np.zeros(n)
    out[:p] = buf
    damp = 0.996 if f < 300 else 0.994
    for i in range(p, n):
        out[i] = damp * 0.5 * (out[i - p] + out[i - p + 1 if i - p + 1 < i else i - p])
    return out / (np.abs(out).max() + 1e-9) * np.minimum(1, np.arange(n) / SR / 0.003)


def epiano(f, dur=1.6):
    return GS.keys(f, dur)


def strings(f, dur, a=0.5, r=1.0):
    n = int((dur + r) * SR)
    t = np.arange(n) / SR
    x = sum((0.6 / k) * np.sin(2 * np.pi * f * k * t * dt) for k in (1, 2, 3) for dt in (1.0, 1.004))
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5 * t)
    x = x * vib
    e = np.minimum(1, t / a) * np.clip((dur + r - t) / r, 0, 1)
    return x * e / 2


# ---------------------------------------------------------------- progressions
PROG = {
    "C": [[48, 52, 55], [45, 48, 52], [41, 45, 48], [43, 47, 50]],          # C Am F G
    "D": [[50, 54, 57], [47, 50, 54], [43, 47, 50], [45, 49, 52]],          # D Bm G A
    "F": [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]],   # Fmaj7 Em7 Dm7 Cmaj7
    "G": [[43, 47, 50], [40, 43, 47], [48, 52, 55], [50, 54, 57]],          # G Em C D
    "Am": [[45, 48, 52], [41, 45, 48], [48, 52, 55], [43, 47, 50]],         # Am F C G
    "Eb": [[51, 55, 58, 62], [48, 51, 55, 58], [44, 48, 51, 55], [46, 50, 53, 56]],  # Ebmaj7 Cm7 Abmaj7 Bb7
    "E": [[52, 56, 59], [49, 52, 56], [45, 49, 52], [47, 51, 54]],          # E C#m A B
    "Bb": [[46, 50, 53], [43, 46, 50], [51, 55, 58], [53, 57, 60]],         # Bb Gm Eb F
}

# name: (instrument, pattern, progression, bpm, octave shift for the pattern)
STYLES = {
    "piano_c": (piano, "figure", "C", 100, 12),
    "music_box_d": (music_box, "arp_up", "D", 96, 24),
    "guitar_g": (pluck, "fingerpick", "G", 90, 12),
    "marimba_f": (marimba, "bounce", "F", 104, 12),
    "lofi_eb": (epiano, "lofi", "Eb", 82, 12),
    "strings_am": (piano, "slow_melody", "Am", 78, 24),
    "kalimba_e": (kalimba, "arp_up", "E", 98, 12),
    "harp_bb": (pluck, "arp_wave", "Bb", 94, 12),
}


def _gain(t, t_end, g0, g1):
    return g0 + (g1 - g0) * prog(t, 0, t_end)


def score(style, dur, t_end, t_warm=14.6, t_line=15.0, start=0.2, loud=1.0):
    inst, pattern, key, bpm, octv = STYLES[style]
    chords = PROG[key]
    n = int(dur * SR)
    mus = np.zeros((n, 2))
    beat = 60 / bpm
    bar = 4 * beat
    g_lo, g_hi = 0.032 * loud, 0.085 * loud
    # pads under everything
    b = 0
    while b * bar < t_end:
        t0 = b * bar
        ch = chords[b % 4]
        g = 0.026 + 0.034 * prog(t0, 0, t_end)
        pad_fn = (lambda f, d: strings(f, d, 0.6, 0.9)) if style == "strings_am" else (lambda f, d: GS.pad(f, d, 0.3, 0.8))
        for k, m in enumerate(ch[:3]):
            mix_in(mus, pad_fn(midi(m), min(bar, t_end - t0)), t0, g * (0.8 if style == "strings_am" else 1), (k - 1) * 0.4)
        if pattern in ("fingerpick", "lofi", "bounce"):
            mix_in(mus, inst(midi(ch[0] - 12), 1.6), t0, _gain(t0, t_end, g_lo, g_hi) * 0.9, -0.1)
        b += 1
    t = start
    i = 0
    eighth = beat / 2
    while t < t_end:
        bi = int(t / bar)
        ch = chords[bi % 4]
        pos = i % 8
        g = _gain(t, t_end, g_lo, g_hi)
        notes = []
        if pattern == "figure":
            fig = [0, 1, 2, 1, 0, 1, 2, 1]
            ups = [ch[0], ch[1], ch[2]]
            notes = [ups[fig[pos]] + octv + (12 if pos in (2,) else 0)]
        elif pattern == "arp_up":
            seq = [0, 1, 2, 3, 4, 3, 2, 1]
            tones = [ch[0], ch[1], ch[2], ch[0] + 12, ch[1] + 12]
            notes = [tones[seq[pos]] + octv - 12]
        elif pattern == "arp_wave":
            seq = [0, 1, 2, 3, 2, 1, 2, 3]
            tones = [ch[0], ch[1], ch[2], ch[0] + 12]
            notes = [tones[seq[pos]] + octv]
        elif pattern == "fingerpick":
            seq = [None, 2, 1, 2, None, 2, 1, 0]
            s = seq[pos]
            if s is not None:
                notes = [ch[s] + octv]
        elif pattern == "bounce":
            seq = [None, 0, 2, None, 1, None, 2, 1]
            s = seq[pos]
            if s is not None:
                notes = [ch[s] + octv]
        elif pattern == "lofi":
            if pos in (0, 3):
                notes = [m + octv - 12 for m in ch]
            elif pos == 6:
                notes = [ch[-1] + octv]
        elif pattern == "slow_melody":
            mel = [0, None, 2, None, 1, None, None, None]
            s = mel[pos]
            if s is not None:
                notes = [ch[s] + octv - 12]
        for k, m in enumerate(notes):
            dur_n = 1.8 if pattern in ("slow_melody", "lofi") else 1.2
            sig = inst(midi(m), dur_n) if inst is not pluck else pluck(midi(m), dur_n, 0.5, i)
            mix_in(mus, sig, t + (0.012 * k if pattern == "lofi" else 0), g * (0.55 if len(notes) > 1 else 1.0),
                   0.25 if k % 2 == 0 else -0.25)
        i += 1
        t += eighth
    if style == "lofi_eb":
        crackle = np.zeros(n)
        rng = np.random.default_rng(5)
        idx = rng.integers(0, n, int(dur * 25))
        crackle[idx] = rng.uniform(-1, 1, len(idx))
        mus[:, 0] += crackle * 0.02
        mus[:, 1] += crackle * 0.02
        hiss = noise(dur, 6, lo=3000, hi=9000) * 0.004
        mus[:, 0] += hiss
        mus[:, 1] += hiss
    # the warm chord and the closing notes, in the key of the first chord
    root = chords[0]
    for k, m in enumerate([root[0] - 12, root[0], root[1], root[2]]):
        sig = strings(midi(m), 2.6, 0.5, 1.4) if style == "strings_am" else GS.pad(midi(m), 3.0, 0.5, 1.6)
        mix_in(mus, sig, t_warm, 0.05, (k - 1.5) * 0.4)
    close = [root[2] + 24, root[0] + 24, root[1] + 12, root[0] + 12]
    for j, m in enumerate(close):
        f = midi(m + (octv - 12))
        sig = pluck(f, 1.6, 0.5, j) if inst is pluck else inst(f, 1.6)
        mix_in(mus, sig, t_line + j * 0.5, 0.05, 0.2)
    return mus
