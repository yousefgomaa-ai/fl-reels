# One-off (owner, 2026-11-17: «عايزين نحط صور»): Commons candidates by category for the rules episodes, a contact sheet each.
import json, urllib.request, urllib.parse, os, re, html, io, traceback
from PIL import Image, ImageDraw
UA = {'User-Agent': 'FootballLegends/1.0 (reels)'}
C = {
 'yellow': ['incategory:"Yellow cards" football', 'referee yellow card association football'],
 'penalty': ['penalty kick association football match', 'penalty kick football goalkeeper dive'],
 'corner': ['corner kick association football match'],
 'throwin': ['throw-in association football match'],
 'keeper': ['goalkeeper catches ball association football match', 'goalkeeper ball hands football match'],
 'shirt': ['footballer celebrates goal shirt', 'football player celebrating goal'],
 'ball': ['association football match ball', 'football ball grass pitch'],
 'goal': ['empty football goal net stadium', 'association football goal posts net'],
 'referee': ['association football referee match whistle'],
 'kickoff': ['kick-off association football centre circle'],
 'line': ['football pitch penalty area line', 'goal line association football'],
 'stadium': ['football stadium match crowd pitch'],
}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40))
out = {}
os.makedirs('probe/img', exist_ok=True)
for k, cats in C.items():
    lst = []
    for cat in cats:
        try:
            u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': cat + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 40,
                'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size|mime', 'iiurlwidth': 300})
            pages = (get(u).get('query') or {}).get('pages') or {}
        except Exception as e: print(k, cat, e); continue
        for p in pages.values():
            ii = (p.get('imageinfo') or [{}])[0]; md = ii.get('extmetadata') or {}
            if ii.get('mime') not in ('image/jpeg', 'image/png') or ii.get('width', 0) < 1000: continue
            lic = (md.get('LicenseShortName') or {}).get('value', '')
            if not re.search(r'CC|Public domain|PD', lic, re.I): continue
            t = p['title']
            if re.search(r'women|woman|female|girls|ladies|frauen|femen|feminin|israel|algeri|american football|rugby|nfl|ncaa|gaelic|aussie|afl|packers|lacrosse|hockey|basketball', t + str((md.get('ImageDescription') or {}).get('value', '')) + str((md.get('Categories') or {}).get('value', '')), re.I): continue
            art = re.sub('<[^>]+>', '', html.unescape((md.get('Artist') or {}).get('value', ''))).strip()[:60]
            lst.append({'title': t, 'thumb': ii.get('thumburl'), 'w': ii['width'], 'h': ii['height'], 'artist': art, 'license': lic})
            if len(lst) >= 12: break
        if len(lst) >= 12: break
    # a contact sheet: 4 x 3, numbered
    sheet = Image.new('RGB', (4 * 300, 3 * 240), (20, 20, 30)); d = ImageDraw.Draw(sheet)
    for i, x in enumerate(lst):
        try:
            im = Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(x['thumb'], headers=UA), timeout=30).read())).convert('RGB')
            im.thumbnail((296, 220)); sheet.paste(im, ((i % 4) * 300 + 2, (i // 4) * 240 + 2)); d.rectangle(((i % 4) * 300, (i // 4) * 240 + 200, (i % 4) * 300 + 40, (i // 4) * 240 + 238), fill=(255, 0, 80)); d.text(((i % 4) * 300 + 8, (i // 4) * 240 + 210), str(i), fill=(255, 255, 255))
        except Exception as e: print(k, i, e)
    sheet.save(f'probe/img/{k}.jpg', quality=80)
    out[k] = lst; print(k, len(lst))
json.dump(out, open('probe/commons.json', 'w'), ensure_ascii=False, indent=1)
