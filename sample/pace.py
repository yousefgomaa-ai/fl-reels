# One-off probe (owner, 2026-11-12): did Salah play Liverpool's league games after 25 Oct (his games count), and the ESPN crest ids.
import json, urllib.request
H = {'User-Agent': 'Mozilla/5.0'}
get = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60).read())
for d in ['20261025', '20261101', '20261108']:
    for e in get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={d}').get('events', []):
        if 'Liverpool' not in e['name']: continue
        s = get(f'https://site.web.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event={e["id"]}')
        for r in s.get('rosters', []):
            for p in r.get('roster', []):
                if 'Salah' in p.get('athlete', {}).get('displayName', ''):
                    print('SALAH', d, e['name'], 'starter', p.get('starter'), 'subbedIn', p.get('subbedIn'), 'active', p.get('active'), [x.get('name') + '=' + str(x.get('value')) for x in p.get('stats', []) if x.get('name') in ('appearances', 'totalGoals', 'subIns')])
for i in [361, 367, 360, 364, 83, 86, 93, 112, 104, 103, 110, 132, 133, 268, 124, 174, 167, 178, 114]:
    try: t = get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/{i}')['team']; print('CREST', i, t.get('displayName'))
    except Exception as ex: print('CREST', i, 'ERR', ex)
