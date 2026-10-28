# Each script line's start in the single reading: its first words found in whisper's word timings, in order.
import json, re, sys, difflib
vt, vj = sys.argv[1], sys.argv[2]
lines = [l.strip() for l in open(vt) if l.strip()]
W = [w for s in json.load(open(vj)) for w in s.get('w', [])]
def norm(t):
    t = re.sub(r'[ً-ْـ،,.:؟!«»]', '', t)
    t = re.sub('[أإآ]', 'ا', t).replace('ة', 'ه').replace('ى', 'ي')
    return t.strip()
words = [norm(w[1]) for w in W]
starts, ptr = [0.0], 0
for ln in lines[1:]:
    first = [norm(x) for x in ln.split()[:3]]
    best, bi = 0, None
    for i in range(ptr, len(words) - 2):
        sc = sum(difflib.SequenceMatcher(None, first[k], words[i + k]).ratio() for k in range(3)) / 3
        if sc > best + 0.001: best, bi = sc, i
        if i > ptr + 60: break
    starts.append(W[bi][0]); ptr = bi + 1
    print(f'{W[bi][0]:7.2f} {best:.2f}  {" ".join(words[bi:bi+3])}  <=  {" ".join(first)}')
end = json.load(open(vj))[-1]['e']
print(json.dumps({'starts': starts, 'end': end}))
