# One-off (2026-10-30): the frames of PSG's full-time reel against the match's scorers.
import json, os, urllib.parse, urllib.request
K = urllib.parse.quote(os.environ.get('REELS_KEY', ''), safe='')
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0)'}
def get(u):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read())
    except Exception as e: print('ERR', u[:80], e); return None
st = get(f'https://api.football-legend.com/v2/reels/status?key={K}') or {}
for r in st.get('reels', []):
    if r.get('id', '').startswith(('live-fd-559644', 'live-fm-5970195', 'match-fd-559644')):
        print(json.dumps({k: r.get(k) for k in ('id', 'status', 'frames', 'seconds', 'readyAt', 'fb', 'ig')}, ensure_ascii=False)[:1500])
for d in ('20261030', '20261029'):
    m = get(f'https://api.football-legend.com/matches?date={d}') or {}
    for e in m.get('events', []) if isinstance(m, dict) else []:
        if str(e.get('id')) in ('fd-559644', 'fm-5970195'):
            print(d, e.get('id'), e.get('leagueSlug'), e['teams']['home']['name'], e.get('goals'), e['teams']['away']['name'], e.get('fixture', {}).get('status'))
