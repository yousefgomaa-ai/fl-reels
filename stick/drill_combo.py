#!/usr/bin/env python3
"""LAZY vs EGO vs WORKER - the combined cut. One person at a time through all three challenges, one flashback each,
the worker's flashback is a montage of all three. Built from raw pieces rendered by drill.py, then sped up 1.25x,
with one music bed across the whole thing.

    python3 stick/drill_combo.py stick/drill/combined.mp4
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "drill", "_pieces")
SPEED = 1.5
MUSIC = os.path.join(HERE, "..", "study", "music", "Undaunted.mp3")


def info(sit):
    out = subprocess.run([sys.executable, "-c", f"import sys; sys.argv=['x','{sit}']; sys.path.insert(0,'{HERE}');"
                          "import drill as D; print(D.T_INTRO, D.T_LINE, D.DUR, *[f'{D.TURN[w][0]},{D.TURN[w][1]}' for w in D.WHO])"],
                         capture_output=True, text=True, check=True).stdout.split()
    t_intro, t_line, dur = map(float, out[:3])
    turns = {w: tuple(map(float, x.split(","))) for w, x in zip(("LAZY", "EGO", "WORKER"), out[3:])}
    return t_intro, t_line, dur, turns


def piece(name, sit, a, b, combo=None, fb=None):
    out = os.path.join(TMP, name + ".mov")
    env = dict(os.environ)
    if combo:
        env["DRILL_COMBO"] = combo
    cmd = [sys.executable, os.path.join(HERE, "drill.py"), sit, "--fb" if fb else "--range", str(a), str(b), out]
    if fb:
        cmd.append(fb)
    subprocess.run(cmd, env=env, check=True, capture_output=True)
    return out


# trims (turn-relative seconds, before the speed-up): start on the action, cut right after the result
TRIM = {("penalty", "LAZY"): (1.7, 3.5), ("penalty", "EGO"): (0.6, 2.85), ("penalty", "WORKER"): (0.1, 1.55),
        ("hoop", "LAZY"): (1.3, 3.25), ("hoop", "EGO"): (0.6, 2.85), ("hoop", "WORKER"): (0.0, 1.8),
        ("pullup", "LAZY"): (0.6, 3.4), ("pullup", "EGO"): (0.6, 3.4), ("pullup", "WORKER"): (0.6, 4.2)}


def main():
    final = sys.argv[1]
    os.makedirs(TMP, exist_ok=True)
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))
    SITS = ["penalty", "hoop", "pullup"]
    I = {s: info(s) for s in SITS}
    parts = []
    n = 1
    for who in ("LAZY", "EGO", "WORKER"):
        for k, sit in enumerate(SITS, 1):
            a, d = I[sit][3][who]
            s0, s1 = TRIM[(sit, who)]
            parts.append(piece(f"{n:02d}_{who}_{sit}", sit, a + s0, a + min(d, s1), combo=f"{who}:{k}"))
            n += 1
        if who != "WORKER":
            parts.append(piece(f"{n:02d}_fb_{who}", "penalty", 0.0, 1.4, fb=who))
            n += 1
    for sit in SITS:
        parts.append(piece(f"{n:02d}_fb_WORKER_{sit}", sit, 0.12, 1.02, fb="WORKER"))
        n += 1
    t_line = I["pullup"][1]
    os.environ["DRILL_TROPHY"] = "1"
    parts.append(piece(f"{n:02d}_end", "pullup", t_line, t_line + 1.3 + 2.1, combo="WORKER:3"))
    del os.environ["DRILL_TROPHY"]
    lst = os.path.join(TMP, "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    raw = os.path.join(TMP, "raw.mov")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw], check=True)
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw],
                                 capture_output=True, text=True).stdout) / SPEED
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-ss", "40", "-i", MUSIC, "-filter_complex",
                    f"[0:v]setpts=PTS/{SPEED},fps=30[v];[0:a]atempo={SPEED},volume=1.0[s];"
                    f"[1:a]atrim=0:{total:.2f},volume=1.5,afade=t=out:st={total - 0.8:.2f}:d=0.8[m];"
                    "[s][m]amix=inputs=2:normalize=0,loudnorm=I=-13:TP=-1.5:LRA=11[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-t", f"{total:.2f}", "-movflags", "+faststart", final], check=True)
    print(final, round(total, 1))
    print('Credit: Music: "Undaunted" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
