# One-off probe (owner, 2026-11-12): Commons photo candidates for the all-time top scorers, as contact sheets to pick by eye.
import json, os, sys, time, urllib.request, urllib.parse, io
from PIL import Image, ImageDraw
H = {'User-Agent': 'FBLegendsBot/1.0 (football stats reels; contact via github)'}
def get(u, raw=False):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60) as r: b = r.read(); return b if raw else json.loads(b)
        except Exception as e: err = e; time.sleep(2 + 3 * i)
    raise err
P = json.load(open('sample/players.json'))
os.makedirs('sample/sheets', exist_ok=True); meta = {}
for slug, qs in P.items():
    seen, cands = set(), []
    for q in qs:
        u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': q + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 8,
            'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size', 'iiurlwidth': 300})
        d = get(u)
        for pg in sorted((d.get('query') or {}).get('pages', {}).values(), key=lambda p: p.get('index', 99)):
            t = pg['title']
            if t in seen: continue
            seen.add(t); ii = pg['imageinfo'][0]; em = ii.get('extmetadata', {})
            cands.append({'file': t[5:], 'thumb': ii['thumburl'], 'w': ii.get('width'), 'h': ii.get('height'), 'lic': em.get('LicenseShortName', {}).get('value', ''), 'artist': em.get('Artist', {}).get('value', '')[:200], 'date': em.get('DateTimeOriginal', {}).get('value', '')[:40]})
        time.sleep(.5)
    cands = cands[:12]; meta[slug] = cands
    W, Hh = 4 * 300, 3 * 340; sheet = Image.new('RGB', (W, Hh), 'white'); dr = ImageDraw.Draw(sheet)
    for i, c in enumerate(cands):
        try: im = Image.open(io.BytesIO(get(c['thumb'], True))).convert('RGB'); im.thumbnail((296, 316)); sheet.paste(im, ((i % 4) * 300 + 2, (i // 4) * 340 + 2))
        except Exception as e: pass
        dr.rectangle([(i % 4) * 300, (i // 4) * 340 + 318, (i % 4) * 300 + 60, (i // 4) * 340 + 338], fill='black'); dr.text(((i % 4) * 300 + 6, (i // 4) * 340 + 322), str(i), fill='yellow')
        time.sleep(.3)
    sheet.save(f'sample/sheets/{slug}.jpg', quality=80); print(slug, len(cands), flush=True)
json.dump(meta, open('sample/sheets/meta.json', 'w'), ensure_ascii=False, indent=1)
