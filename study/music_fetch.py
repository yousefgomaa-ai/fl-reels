# Download chosen licensed tracks (incompetech, CC BY 4.0) into study/music/ (runs in GitHub Actions).
# Credit line for any video that uses one: "<Title>" Kevin MacLeod (incompetech.com)
#   Licensed under Creative Commons: By Attribution 4.0 License  http://creativecommons.org/licenses/by/4.0/
import json, os, subprocess, urllib.parse
OUT = "study/music"
WANT = ["Eternal Hope", "Reunited", "Bittersweet", "Sad Trio", "Touching Moments Four - Melody", "Immersed"]
cat = {p["title"]: p for p in json.load(open(f"{OUT}/catalog.json"))["incompetech"]}
got = []
for t in WANT:
    p = cat.get(t)
    if not p:
        got.append({"title": t, "err": "not in catalog"})
        continue
    fn = p["filename"]
    url = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/" + urllib.parse.quote(fn)
    dst = os.path.join(OUT, fn)
    r = subprocess.run(["curl", "-sSfL", "--max-time", "120", "-o", dst, url], capture_output=True, text=True)
    got.append({"title": t, "file": fn, "url": url, "ok": r.returncode == 0 and os.path.exists(dst),
                "bytes": os.path.getsize(dst) if os.path.exists(dst) else 0, "err": r.stderr[-200:]})
json.dump(got, open(f"{OUT}/fetched.json", "w"), indent=1)
print(got)
