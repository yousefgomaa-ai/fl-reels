# One-off (2026-11-17): FB Legends today (Nations League boards, the photo post), then the leagues' return: a November
# fixtures reel for each of the big five (owner: «جهز شويه ريلز تنزل تجهيزا لعودة الدوريات»), each asked on Telegram.
import json, os, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
def get(path, **q):
    q['key'] = K
    u = 'https://api.football-legend.com' + path + '?' + urllib.parse.urlencode(q)
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'fl-probe'}), timeout=120)
        return json.loads(r.read().decode())
    except Exception as e:
        return {'error': str(e)}
x = get('/v2/fben/dry', kinds='none', snap='natlive')
print('PROBE natlive', json.dumps({k: x.get(k) for k in ('snap', 'marks', 'error')}, ensure_ascii=False)[:3000])
x = get('/v2/fben/dry', kinds='none', snap='fben:v1:reel:en-pick-20261117', job='en-pick-20261117')
print('PROBE pick', json.dumps({k: x.get(k) for k in ('snap', 'job', 'error')}, ensure_ascii=False)[:800])
for lg in ['eng.1', 'esp.1', 'ita.1', 'ger.1', 'fra.1']:
    x = get('/v2/fben/dry', kinds='none', special='month-' + lg)
    print('PROBE special', lg, json.dumps(x.get('special', x), ensure_ascii=False)[:400])
