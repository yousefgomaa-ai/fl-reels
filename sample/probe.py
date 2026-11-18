# One-off (2026-11-18): league goals this season and club now for the «back from the break» stars (FotMob player pages).
import json, gzip, urllib.request
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36'}
def get(u):
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60).read()
        if b[:2] == b'\x1f\x8b': b = gzip.decompress(b)
        return json.loads(b)
    except Exception as e: return {'error': str(e)}
for name, pid in [('Vinicius', 846033), ('Wirtz', 1152455), ('Haaland', 737066), ('Kane', 194165), ('Salah', 292462)]:
    d = get(f'https://www.fotmob.com/api/data/playerData?id={pid}')
    if 'error' in d: print('PROBE', name, d); continue
    ml = d.get('mainLeague') or {}
    print('PROBE', name, '|', (d.get('primaryTeam') or {}).get('teamName'), '|', ml.get('leagueName'), ml.get('season'), '|', json.dumps([[s.get('title'), s.get('value')] for s in ml.get('stats', [])], ensure_ascii=False)[:300])
