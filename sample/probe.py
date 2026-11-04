# One-off (2026-11-04): Commons candidates for the Al Ahly history video, small thumbs + credits in sample/pl/ahly/.
import json, os, re, time, urllib.parse, urllib.request
UA = {'User-Agent': 'FootballLegends/1.0 (football-legend.com)'}
os.makedirs('sample/pl/ahly', exist_ok=True)
QS = ['Al Ahly SC', 'Al Ahly fans', 'Al Ahly Cairo stadium', 'Cairo International Stadium', 'Mahmoud El Khatib', 'Mohamed Aboutrika',
      'Mohamed Magdy Afsha', 'Al Ahly CAF Champions League', 'Al Ahly club Gezira', 'Mohamed Abdelmonem', 'Al Ahly Zamalek', 'Al Ahly trophy']
out = {}
n = 0
for q in QS:
    time.sleep(2)
    r = json.loads(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json',
        'generator': 'search', 'gsrsearch': q + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 10, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size', 'iiurlwidth': 320}), headers=UA), timeout=30).read())
    for p in sorted((r.get('query') or {}).get('pages', {}).values(), key=lambda x: x.get('index', 0)):
        t = p['title']
        if t in out: continue
        ii = p['imageinfo'][0]; em = ii.get('extmetadata', {})
        try:
            time.sleep(1); open(f'sample/pl/ahly/{n:03d}.jpg', 'wb').write(urllib.request.urlopen(urllib.request.Request(ii['thumburl'], headers=UA), timeout=30).read())
        except Exception as e:
            print(q, t, 'thumb failed', e); continue
        out[t] = {'n': n, 'q': q, 'w': ii.get('width'), 'h': ii.get('height'), 'artist': re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', '')).strip()[:80],
                  'license': em.get('LicenseShortName', {}).get('value', ''), 'desc': re.sub('<[^>]+>', '', em.get('ImageDescription', {}).get('value', '')).strip()[:160]}
        print(n, q, '|', t, '|', out[t]['license'], '|', out[t]['w'], 'x', out[t]['h']); n += 1
json.dump(out, open('sample/pl/ahly/list.json', 'w'), ensure_ascii=False, indent=1)
