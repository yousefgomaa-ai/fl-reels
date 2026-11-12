# One-off (owner, 2026-11-12: Leicester 2015-16 story reel): Commons candidates for each subject, small thumbs committed
# back to this branch to be checked by eye. Never merged.
import json, os, urllib.parse, urllib.request, urllib.error
UA = {'User-Agent': 'FootballLegendsReels/1.0 (https://football-legend.com)'}
import time
def raw(u):
    for t in range(6):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(10 * (t + 1))
    raise RuntimeError('429 ' + u)
def get(u):
    time.sleep(1); return json.loads(raw(u))
Q = {'vardy': ['Jamie Vardy Leicester', 'Jamie Vardy 2016', 'Jamie Vardy 2015'],
     'mahrez': ['Riyad Mahrez Leicester', 'Riyad Mahrez 2016', 'Mahrez 2015'],
     'kante': ['Kante Leicester', 'NGolo Kante 2016', "N'Golo Kanté 2015"],
     'ranieri': ['Claudio Ranieri Leicester', 'Ranieri 2016', 'Claudio Ranieri 2015'],
     'stadium': ['King Power Stadium', 'Leicester City stadium aerial'],
     'parade': ['Leicester City 2016 parade', 'Leicester City champions 2016', 'Leicester City trophy 2016'],
     'hazard': ['Eden Hazard Chelsea', 'Eden Hazard 2016']}
os.makedirs('probe/th', exist_ok=True); out = {}
for k, qs in Q.items():
    seen = []
    for q in qs:
        r = get('https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srlimit=15&format=json&srsearch=' + urllib.parse.quote(q))
        for x in r['query']['search']:
            t = x['title']
            if t not in seen and t.lower().endswith(('.jpg', '.jpeg', '.png')): seen.append(t)
    rows = []
    for i, t in enumerate(seen[:10]):
        ii = get('https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=360&format=json&titles=' + urllib.parse.quote(t))
        p = next(iter(ii['query']['pages'].values()))['imageinfo'][0]; m = p.get('extmetadata', {})
        g = lambda n: (m.get(n, {}).get('value') or '')[:120]
        fn = f'probe/th/{k}-{i:02d}.jpg'
        try:
            time.sleep(2); open(fn, 'wb').write(raw(p['thumburl']))
        except Exception as e:
            fn = 'ERR ' + str(e)
        rows.append({'n': fn, 'title': t, 'w': p['width'], 'h': p['height'], 'artist': g('Artist'), 'lic': g('LicenseShortName'), 'date': g('DateTimeOriginal')})
        print(k, i, t, p['width'], p['height'], g('LicenseShortName'), '|', g('Artist')[:60], '|', g('DateTimeOriginal')[:20])
    out[k] = rows
json.dump(out, open('probe/th/index.json', 'w'), indent=1)
