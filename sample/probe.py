# One-off (2026-10-30): logos and Commons photo candidates for the YouTube long-video samples.
import json, os, re, time, urllib.parse, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0; football-legend.com)'}
def raw(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read()
os.makedirs('sample/yt/logo', exist_ok=True); os.makedirs('sample/yt/cand', exist_ok=True)
d = json.load(open('sample/yt/data.json'))
ids = {r['id'] for r in d['eng.1:table']} | {'86'}
for i in sorted(ids):
    try: open(f'sample/yt/logo/{i}.png', 'wb').write(raw(f'https://a.espncdn.com/i/teamlogos/soccer/500/{i}.png'))
    except Exception as e: print('logo', i, e)
Q = {'distefano': 'Alfredo Di Stéfano', 'puskas': 'Ferenc Puskás Real Madrid', 'bernabeu': 'Santiago Bernabéu Stadium', 'rm2014': 'Real Madrid Champions League 2014',
     'ramos': 'Sergio Ramos Real Madrid', 'ronaldo': 'Cristiano Ronaldo Real Madrid', 'zidane': 'Zinedine Zidane Real Madrid coach', 'rmtrophy': 'Real Madrid Champions League trophy celebration',
     'vinicius': 'Vinícius Júnior Real Madrid', 'wembley': 'Wembley Stadium', 'anfield': 'Anfield stadium', 'emirates': 'Emirates Stadium Arsenal', 'arteta': 'Mikel Arteta',
     'iraola': 'Andoni Iraola', 'villapark': 'Villa Park', 'oldtrafford': 'Old Trafford stadium', 'jackson': 'Nicolas Jackson', 'haaland': 'Erling Haaland Manchester City', 'isak': 'Alexander Isak'}
cand = {}
for k, q in Q.items():
    time.sleep(2)
    try:
        r = json.loads(raw('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': q + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 8,
            'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size', 'iiurlwidth': 480})))
        pages = sorted((r.get('query') or {}).get('pages', {}).values(), key=lambda p: p.get('index', 0))
        cand[k] = []
        for n, p in enumerate(pages):
            ii = p['imageinfo'][0]; em = ii.get('extmetadata', {})
            lic = em.get('LicenseShortName', {}).get('value', '')
            if not re.search(r'CC|Public domain|PD', lic, re.I): continue
            time.sleep(1)
            open(f'sample/yt/cand/{k}-{n}.jpg', 'wb').write(raw(ii['thumburl']))
            cand[k].append({'n': n, 'title': p['title'], 'w': ii.get('width'), 'h': ii.get('height'), 'artist': re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', '')).strip()[:80], 'license': lic})
        print(k, len(cand[k]))
    except Exception as e: print(k, 'failed', e)
json.dump(cand, open('sample/yt/cand.json', 'w'), ensure_ascii=False, indent=1)
