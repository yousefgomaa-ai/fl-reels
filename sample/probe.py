# One-off (2026-11-10): the status the site's API gives Thursday's Colombian league matches (shown as finished 0:0).
import json, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0; football-legend.com)'}
import os
os.makedirs('sample/pl', exist_ok=True)
out = []
for d in ['20261112', '20261113']:
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://api.football-legend.com/matches?date={d}', headers=UA), timeout=40).read())
    except Exception as e:
        out.append(f'{d} failed {e}'); continue
    ev = r.get('events') or r.get('matches') or r if isinstance(r, list) else (r.get('events') or r.get('matches') or [])
    for m in ev:
        if 'col' not in str(m.get('leagueSlug', '')) and 'colomb' not in json.dumps(m.get('league', ''), ensure_ascii=False).lower(): continue
        out.append(json.dumps({'d': d, 'id': m.get('id') or m.get('fixture', {}).get('id'), 'slug': m.get('leagueSlug'), 'date': m.get('fixture', {}).get('date'), 'status': m.get('fixture', {}).get('status'), 'goals': m.get('goals'), 'home': m.get('teams', {}).get('home', {}).get('name')}, ensure_ascii=False))
    out.append(f'{d}: {len(ev)} events, keys {list(r.keys())[:8] if isinstance(r, dict) else "list"}')
open('sample/pl/col-status.txt', 'w').write('\n'.join(out)); print('\n'.join(out))
