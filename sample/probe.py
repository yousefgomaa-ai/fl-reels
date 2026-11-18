# One-off (2026-11-18): (1) the Nations League final tables after #705 (dry run, why); (2) the six leagues' full
# scorer lists (FotMob), for the stars who scored in the break: club now and league goals this season.
import json, os, time, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36'}
def get(u, h=H, t=60):
    try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=t))
    except Exception as e: return {'error': str(e)}
FM = {'eng.1': 47, 'esp.1': 87, 'ita.1': 55, 'ger.1': 54, 'fra.1': 53, 'tur.1': 71}
for lg, fid in FM.items():
    d = get(f'https://www.fotmob.com/api/data/leagues?id={fid}')
    st = (d.get('stats') or {}).get('players') or []
    for cat in st[:2]:
        url = cat.get('fetchAllUrl') or ''
        print('PROBE cat', lg, cat.get('header'), cat.get('name'), url[:160])
        if url:
            a = get(url if url.startswith('http') else 'https://www.fotmob.com' + url)
            lst = ((a.get('TopLists') or [{}])[0].get('StatList') or [])
            print('PROBE list', lg, cat.get('name'), json.dumps([[r.get('ParticipantName'), r.get('TeamName'), r.get('StatValue'), r.get('ParticiantId') or r.get('ParticipantId')] for r in lst[:25]], ensure_ascii=False) if lst else str(a)[:200])
time.sleep(30)
x = get('https://api.football-legend.com/v2/fben/dry?' + urllib.parse.urlencode({'key': K, 'kinds': 'nlfinal'}), {'User-Agent': 'fl-probe'}, 180)
r = x.get('result', x)
print('PROBE nlfinal', r.get('nlfinal') if isinstance(r, dict) else '', json.dumps(r.get('nlfinalWhy') if isinstance(r, dict) else r, ensure_ascii=False)[:800])
for j in (x.get('jobs') or [])[:1]:
    print('PROBE caption', j.get('caption', '')[:900])
    for g in (j.get('anim') or {}).get('groups', []): print('PROBE group', g.get('g'), json.dumps(g.get('rows'), ensure_ascii=False)[:600], '|', g.get('key'), '|', json.dumps(g.get('res'), ensure_ascii=False)[:300])
