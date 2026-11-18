# One-off (2026-11-18): did last night's Nations League final tables reel get made (fbEnNlFinal)? And what would it say now.
import json, os, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
def get(**q):
    q['key'] = K
    try: return json.loads(urllib.request.urlopen(urllib.request.Request('https://api.football-legend.com/v2/fben/dry?' + urllib.parse.urlencode(q), headers={'User-Agent': 'fl-probe'}), timeout=120).read())
    except Exception as e: return {'error': str(e)}
x = get(kinds='none', snap='fben:nlfinal:2026-11-17', job='en-nlfinal-20261117')
print('PROBE mark', json.dumps(x, ensure_ascii=False)[:800])
x = get(kinds='nlfinal')
print('PROBE dry', json.dumps(x, ensure_ascii=False)[:3000])
