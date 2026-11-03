# One-off (2026-11-03): how the Egyptian cup matches are named in the API (owner: the League Cup shows as «كأس مصر»).
import json, os, urllib.request
out = []
for d in ['20261020', '20261022', '20261025', '20261027', '20261029', '20261101', '20261103', '20261104', '20261105', '20261106', '20261110']:
    try:
        j = json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.football-legend.com/matches?date={d}', headers={'User-Agent': 'fl-probe'}), timeout=120))
    except Exception as e:
        out.append({'d': d, 'err': str(e)}); continue
    for m in (j.get('events') or j.get('response') or []):
        s = json.dumps(m, ensure_ascii=False)
        if m.get('leagueSlug', '').startswith('egy') or 'EGY' in s or 'Egypt' in s:
            lg = m.get('league')
            out.append({'d': d, 'id': m.get('id'), 'slug': m.get('leagueSlug'), 'league': lg, 'fm': m.get('fmLeague'), 'h': m.get('teams', {}).get('home', {}).get('name'), 'a': m.get('teams', {}).get('away', {}).get('name')})
os.makedirs('sample/pl', exist_ok=True)
json.dump(out, open('sample/pl/egy-cups.json', 'w'), ensure_ascii=False, indent=1)
print(len(out))
