import json, urllib.request
def get(u):
    r = urllib.request.Request(u, headers={'User-Agent': 'fl-check/1.0'})
    with urllib.request.urlopen(r, timeout=60) as x: return json.loads(x.read().decode())
S = get('https://site.api.espn.com/apis/v2/sports/soccer/uefa.nations/standings?season=2026')
def groups(o):
    for c in o.get('children', []):
        yield c
        yield from groups(c)
print('SEASON', S.get('seasons', S.get('season')))
for g in groups(S):
    st = (g.get('standings') or {}).get('entries') or []
    if not st: continue
    print('\n==', g.get('name'), g.get('abbreviation'))
    for e in st:
        s = {x['name']: x.get('displayValue') for x in e.get('stats', [])}
        print('  ', e['team']['displayName'], '| P', s.get('gamesPlayed'), 'W', s.get('wins'), 'D', s.get('ties'), 'L', s.get('losses'), 'GF', s.get('pointsFor'), 'GA', s.get('pointsAgainst'), 'GD', s.get('pointDifferential'), 'PTS', s.get('points'), '| rank', s.get('rank'), '| note', (e.get('note') or {}).get('description'))
print('\n==== SCOREBOARD')
import datetime
d = datetime.date(2026, 9, 1)
seen = set()
while d <= datetime.date(2026, 11, 18):
    try:
        for e in get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.nations/scoreboard?dates={d:%Y%m%d}&limit=100').get('events', []):
            if e['id'] in seen: continue
            seen.add(e['id']); c = e['competitions'][0]; cc = c['competitors']
            h = [x for x in cc if x['homeAway'] == 'home'][0]; a = [x for x in cc if x['homeAway'] == 'away'][0]
            print(e['date'], e['id'], h['team']['displayName'], h.get('score'), '-', a.get('score'), a['team']['displayName'], '|', e['status']['type']['name'], '|', (c.get('venue') or {}).get('fullName'), '|', c.get('groups', {}).get('abbreviation') if isinstance(c.get('groups'), dict) else '', '|', ' '.join(n.get('headline','') for n in c.get('notes', [])))
    except Exception as ex: print('ERR', d, ex)
    d += datetime.timedelta(days=1)
