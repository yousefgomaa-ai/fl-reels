# One-off (2026-11-17): no FB Legends reel went out today. Read-only: the last reel jobs and their state, and the page's day counts.
import json, os, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
def get(path, **q):
    q['key'] = K
    u = 'https://api.football-legend.com' + path + '?' + urllib.parse.urlencode(q)
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'fl-probe'}), timeout=90)
        return json.loads(r.read().decode())
    except Exception as e:
        return {'error': str(e)}
for d in ['2026-11-15', '2026-11-16', '2026-11-17']:
    x = get('/v2/fben/dry', kinds='none', snap='fben:posts:' + d)
    print('PROBE posts', d, json.dumps(x.get('snap', x), ensure_ascii=False)[:600])
s = get('/v2/reels/status')
print('PROBE status', json.dumps(s, ensure_ascii=False)[:6000])
