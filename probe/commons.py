# One-off (owner, 2026-11-17: «عايزين نحط صور»): Commons candidates for the «قانون في 20 ثانية» episodes, small copies
# and credits to check by eye.
import json, urllib.request, urllib.parse, os, re, html
UA = {'User-Agent': 'FootballLegends/1.0 (reels; contact via site)'}
Q = {
 'shirtoff': 'footballer shirt off goal celebration', 'yellow': 'referee showing yellow card football', 'keeperball': 'goalkeeper holding ball football match',
 'jewel': 'football player earring', 'kickoff': 'kick-off football centre circle', 'goalkick': 'goal kick goalkeeper football', 'throwin': 'throw-in football match',
 'corner': 'corner kick football', 'penalty': 'penalty kick football goalkeeper', 'post': 'football hits post goal', 'keepercatch': 'goalkeeper catches ball',
 'keeperthrow': 'goalkeeper throws ball', 'goalnet': 'football goal net', 'penaltyspot': 'penalty spot football pitch', 'matchball': 'football match ball',
 'lineup': 'football team lineup before match', 'referee': 'football referee whistle match', 'goalline': 'ball on goal line football', 'pitchlines': 'football pitch penalty area lines',
}
out = {}
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))
for k, q in Q.items():
    u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': q + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 8,
        'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size', 'iiurlwidth': 360})
    try: pages = (get(u).get('query') or {}).get('pages') or {}
    except Exception as e: print(k, e); continue
    lst = []
    for p in sorted(pages.values(), key=lambda p: p.get('index', 99)):
        ii = (p.get('imageinfo') or [{}])[0]; md = ii.get('extmetadata') or {}
        if ii.get('width', 0) < 900: continue
        art = re.sub('<[^>]+>', '', html.unescape((md.get('Artist') or {}).get('value', ''))).strip()[:60]
        lic = (md.get('LicenseShortName') or {}).get('value', '')
        if not re.search(r'CC|Public domain|PD', lic, re.I): continue
        n = len(lst); fn = f'probe/img/{k}-{n}.jpg'; os.makedirs('probe/img', exist_ok=True)
        try:
            urllib.request.urlretrieve if False else None
            data = urllib.request.urlopen(urllib.request.Request(ii['thumburl'], headers=UA), timeout=30).read(); open(fn, 'wb').write(data)
        except Exception as e: print(k, 'thumb', e); continue
        lst.append({'n': n, 'title': p['title'], 'w': ii.get('width'), 'h': ii.get('height'), 'artist': art, 'license': lic})
        if len(lst) >= 5: break
    out[k] = lst; print(k, len(lst))
json.dump(out, open('probe/commons.json', 'w'), ensure_ascii=False, indent=1)
