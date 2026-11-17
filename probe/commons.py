# One-off (owner, 2026-11-17: «لو في فيديوهات في ويكيميديا ممكن ندمجها»): Commons football video clips, a still of each.
import json, urllib.request, urllib.parse, re, html, subprocess, os
UA = {'User-Agent': 'FootballLegends/1.0 (reels)'}
Q = ['penalty kick football', 'corner kick football', 'throw-in football', 'goalkeeper save football', 'referee yellow card', 'football goal celebration', 'football match stadium', 'football free kick', 'football skills', 'football fans stadium']
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40))
out = []; seen = set(); os.makedirs('probe/img', exist_ok=True)
for q in Q:
    u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': q + ' filetype:video', 'gsrnamespace': 6, 'gsrlimit': 20,
        'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size|mime', 'iiurlwidth': 320})
    try: pages = (get(u).get('query') or {}).get('pages') or {}
    except Exception as e: print(q, e); continue
    n = 0
    for p in pages.values():
        t = p['title']; ii = (p.get('imageinfo') or [{}])[0]; md = ii.get('extmetadata') or {}
        if t in seen: continue
        txt = t + str((md.get('ImageDescription') or {}).get('value', '')) + str((md.get('Categories') or {}).get('value', ''))
        if re.search(r'women|woman|female|girls|ladies|frauen|femen|israel|algeri|american football|rugby|nfl|ncaa|gaelic|afl|futsal|beach', txt, re.I): continue
        if not re.search(r'football|soccer|fútbol|fussball|futebol|calcio', txt, re.I): continue
        seen.add(t); n += 1
        lic = (md.get('LicenseShortName') or {}).get('value', '')
        out.append({'q': q, 'title': t, 'w': ii.get('width'), 'h': ii.get('height'), 'dur': ii.get('duration'), 'lic': lic, 'thumb': ii.get('thumburl')})
    print(q, n)
for i, x in enumerate(out[:40]):
    try: open(f'probe/img/v{i}.jpg', 'wb').write(urllib.request.urlopen(urllib.request.Request(x['thumb'], headers=UA), timeout=30).read())
    except Exception as e: pass
json.dump(out, open('probe/videos.json', 'w'), ensure_ascii=False, indent=1)
from PIL import Image, ImageDraw
sheet = Image.new('RGB', (5 * 260, 8 * 170), (20, 20, 30)); d = ImageDraw.Draw(sheet)
for i in range(40):
    try: im = Image.open(f'probe/img/v{i}.jpg').convert('RGB'); im.thumbnail((256, 150)); sheet.paste(im, ((i % 5) * 260, (i // 5) * 170)); d.text(((i % 5) * 260 + 4, (i // 5) * 170 + 152), str(i), fill=(255, 80, 120))
    except Exception: pass
sheet.save('probe/videos.jpg', quality=80)
