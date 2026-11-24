# Licensed music catalogs for the reels (runs in GitHub Actions; the sandbox has no open internet).
#  - incompetech.com (Kevin MacLeod): CC BY 4.0 - usable on monetized YouTube with a credit line in the description.
#  - freepd.com: public domain (CC0) - no credit needed.
# Writes study/music/catalog.json (titles, moods, tempo, instruments, file urls). Downloads nothing big.
import json, os, re, subprocess, sys
OUT = "study/music"
os.makedirs(OUT, exist_ok=True)


def get(url):
    r = subprocess.run(["curl", "-sSfL", "--max-time", "60", "-A", "Mozilla/5.0 (research script)", url],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


cat = {"incompetech": [], "freepd": [], "errors": []}
raw = get("https://incompetech.com/music/royalty-free/pieces.json")
try:
    pieces = json.loads(raw)
    for p in pieces:
        cat["incompetech"].append({k: p.get(k) for k in ("title", "filename", "genre", "feel", "bpm", "instruments",
                                                          "length", "description", "isrc")})
except Exception as e:
    cat["errors"].append(f"incompetech: {e}; got {len(raw)} bytes")
home = get("https://freepd.com/")
pages = sorted(set(re.findall(r'href="(/?[a-zA-Z0-9_\-]+\.php)"', home)))
for pg in pages:
    url = "https://freepd.com/" + pg.lstrip("/")
    html = get(url)
    for m in re.finditer(r'href="([^"]+\.mp3)"', html):
        href = m.group(1)
        full = href if href.startswith("http") else "https://freepd.com/" + href.lstrip("/")
        cat["freepd"].append({"category": pg.replace(".php", "").strip("/"), "url": full,
                              "title": os.path.basename(href).replace("%20", " ").replace(".mp3", "")})
json.dump(cat, open(f"{OUT}/catalog.json", "w"), indent=1)
print(len(cat["incompetech"]), "incompetech;", len(cat["freepd"]), "freepd;", cat["errors"])
