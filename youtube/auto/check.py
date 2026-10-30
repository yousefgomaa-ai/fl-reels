# Each narration line found in whisper's reading of the one voice file: its start (the scene's start), its captions, and
# the numbers heard in it. Every number of the script must be heard where its line is read (owner, 2026-10-30: a number
# read wrong is never published; the video is held and the owner told).
import difflib, re
from collections import Counter
from arnum import norm, numbers_in

LEAD = 0.5  # make.sh starts the voice half a second in


def key(t):
    t = re.sub(r'[^\w]', '', norm(t))
    for p in ('وال', 'بال', 'ال', 'و'):
        if t.startswith(p) and len(t) - len(p) >= 2:
            return t[len(p):]
    return t


def toks(text):
    return [w for w in re.split(r'\s+', text) if re.sub(r'[^\w]', '', w)]


def align(lines, words, dur):
    """lines: script texts; words: whisper's [start, end, word]. Returns each line's start, coverage and the token map."""
    S, owner = [], []
    for i, l in enumerate(lines):
        for w in toks(l):
            S.append(key(w)); owner.append(i)
    Wk = [key(w[2]) for w in words]
    sm = difflib.SequenceMatcher(None, S, Wk, autojunk=False)
    at = {}
    for b in sm.get_matching_blocks():
        for k in range(b.size):
            at[b.a + k] = b.b + k
    # Near misses (a letter heard differently) count too: a token between two matched ones, similar enough.
    for si in range(len(S)):
        if si in at: continue
        lo = max([at[x] for x in at if x < si], default=-1) + 1
        hi = min([at[x] for x in at if x > si], default=len(Wk))
        best = max(range(lo, hi), key=lambda wi: difflib.SequenceMatcher(None, S[si], Wk[wi]).ratio(), default=None) if hi - lo <= 6 else None
        if best is not None and difflib.SequenceMatcher(None, S[si], Wk[best]).ratio() >= 0.75:
            at[si] = best
    starts, cover = [], []
    for i in range(len(lines)):
        idx = [si for si in range(len(S)) if owner[si] == i]
        hit = [at[si] for si in idx if si in at]
        cover.append(len(hit) / max(1, len(idx)))
        starts.append(words[min(hit)][0] if hit else None)
    # A line with nothing heard takes its place between its neighbours, by its length.
    for i, s in enumerate(starts):
        if s is None:
            prev = next((starts[j] for j in range(i - 1, -1, -1) if starts[j] is not None), 0.0)
            nxt = next((starts[j] for j in range(i + 1, len(starts)) if starts[j] is not None), dur)
            starts[i] = prev + (nxt - prev) * 0.5
    starts[0] = 0.0
    for i in range(1, len(starts)):
        starts[i] = max(starts[i], starts[i - 1] + 1.0)
    return starts, cover, at, owner


def numbers_check(lines, nums, words, starts, dur):
    """The numbers of each line not heard in its window (a second either side): {line: [missing]}."""
    bad = {}
    for i in range(len(lines)):
        if not nums[i]: continue
        a = starts[i] - 1.0
        b = (starts[i + 1] if i + 1 < len(starts) else dur) + 1.0
        heard = numbers_in(' '.join(w[2] for w in words if a <= w[0] <= b))
        miss = Counter(n for n in nums[i] if n is not None) - Counter(heard)
        if miss: bad[i] = sorted(miss.elements())
    return bad


def captions(lines, starts, dur, words, at, owner):
    """Short captions (a clause each, ten words at most), timed by their first word heard."""
    caps, si = [], 0
    for i, l in enumerate(lines):
        end = starts[i + 1] if i + 1 < len(starts) else dur
        ws = toks(l)
        chunks, cur = [], []
        for w in ws:
            cur.append(w)
            if len(cur) >= 10 or re.search('[،,.:؛؟!]$', w) and len(cur) >= 4:
                chunks.append(cur); cur = []
        if cur:
            if chunks and len(cur) < 3: chunks[-1] += cur
            else: chunks.append(cur)
        t0, base = [], si
        for c in chunks:
            hit = [at[x] for x in range(si, si + len(c)) if x in at]
            t0.append(words[min(hit)][0] if hit else None); si += len(c)
        for k in range(len(chunks)):
            if t0[k] is None: t0[k] = starts[i] + (end - starts[i]) * sum(len(c) for c in chunks[:k]) / max(1, len(ws))
        t0[0] = starts[i]
        for k, c in enumerate(chunks):
            s = max(t0[k], caps[-1][1] if caps else 0)
            e = min(t0[k + 1] if k + 1 < len(chunks) else end, end)
            if e - s > 0.3: caps.append([round(s, 2), round(e, 2), re.sub('[.،]$', '', ' '.join(c))])
    return caps


def chapters(lines, chaps, starts):
    """YouTube chapters: the first at 0:00, ten seconds each at least."""
    out = []
    for i, c in enumerate(chaps):
        if not c: continue
        t = 0 if not out else int(starts[i] + LEAD)
        if out and t - out[-1][0] < 10: continue
        out.append([t, c])
    return out if len(out) >= 3 else []


def stamp(t):
    return f'{t // 60}:{t % 60:02d}'
