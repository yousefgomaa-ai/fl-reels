# One-off (2026-11-11): Commons candidates for the Liverpool history video, small thumbs + credits in sample/pl/lfc/.
import json, os, re, time, urllib.parse, urllib.request
UA = {'User-Agent': 'FootballLegends/1.0 (football-legend.com)'}
os.makedirs('sample/pl/lfc', exist_ok=True)
QS = ['Anfield stadium', 'Liverpool FC 1977', 'Liverpool European Cup', 'Kenny Dalglish Liverpool', 'Steven Gerrard Liverpool', 'Jerzy Dudek', 'Ataturk Olympic Stadium',
      'Mohamed Salah Liverpool', 'Jürgen Klopp Liverpool', 'Liverpool Champions League 2019 parade', 'Divock Origi Liverpool', 'Bob Paisley']
out = {}
n = 0
for q in QS:
    time.sleep(2)
    r = json.loads(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json',
        'generator': 'search', 'gsrsearch': q + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 8, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size', 'iiurlwidth': 320}), headers=UA), timeout=30).read())
    for p in sorted((r.get('query') or {}).get('pages', {}).values(), key=lambda x: x.get('index', 0)):
        t = p['title']
        if t in out: continue
        ii = p['imageinfo'][0]; em = ii.get('extmetadata', {})
        try:
            time.sleep(1); open(f'sample/pl/lfc/{n:03d}.jpg', 'wb').write(urllib.request.urlopen(urllib.request.Request(ii['thumburl'], headers=UA), timeout=30).read())
        except Exception as e:
            print(q, t, 'thumb failed', e); continue
        out[t] = {'n': n, 'q': q, 'w': ii.get('width'), 'h': ii.get('height'), 'artist': re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', '')).strip()[:80],
                  'license': em.get('LicenseShortName', {}).get('value', ''), 'desc': re.sub('<[^>]+>', '', em.get('ImageDescription', {}).get('value', '')).strip()[:160]}
        n += 1
json.dump(out, open('sample/pl/lfc/list.json', 'w'), ensure_ascii=False, indent=1)
