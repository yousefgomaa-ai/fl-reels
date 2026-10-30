# One-off (2026-10-30): data for the YouTube long-video samples (round review, big-match preview).
import json, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0)'}
def get(u):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read())
    except Exception as e: print('ERR', u[:90], e); return {}
B = 'https://site.api.espn.com/apis/site/v2/sports/soccer'
out = {}
for lg in ['eng.1', 'esp.1', 'egy.1']:
    sb = get(f'{B}/{lg}/scoreboard?dates=20261016-20261029&limit=100')
    ev = []
    for e in sb.get('events', []):
        c = e['competitions'][0]
        comp = {x['homeAway']: {'name': x['team']['displayName'], 'id': x['team']['id'], 'score': x.get('score'), 'logo': x['team'].get('logo')} for x in c['competitors']}
        goals = [{'min': d.get('clock', {}).get('displayValue'), 'team': d.get('team', {}).get('id'), 'who': [a.get('displayName') for a in d.get('athletesInvolved', [])], 'pen': d.get('penaltyKick'), 'og': d.get('ownGoal')} for d in c.get('details', []) if d.get('scoringPlay')]
        ev.append({'id': e['id'], 'date': e['date'], 'status': c['status']['type']['name'], 'home': comp.get('home'), 'away': comp.get('away'), 'goals': goals, 'venue': c.get('venue', {}).get('fullName'), 'att': c.get('attendance')})
    out[lg + ':past'] = ev
    print(lg, 'past', len(ev))
    for x in ev: print('  ', x['date'][:10], x['home']['name'], x['home']['score'], '-', x['away']['score'], x['away']['name'], x['status'])
    st = get(f'https://site.api.espn.com/apis/v2/sports/soccer/{lg}/standings')
    rows = []
    for ch in st.get('children', [])[:1]:
        for en in ch.get('standings', {}).get('entries', []):
            s = {x['name']: x.get('value') for x in en.get('stats', [])}
            rows.append({'team': en['team']['displayName'], 'id': en['team']['id'], **{k: s.get(k) for k in ('rank', 'gamesPlayed', 'wins', 'ties', 'losses', 'pointsFor', 'pointsAgainst', 'points')}})
    out[lg + ':table'] = rows
    for r in rows[:6]: print('   T', r)
for lg in ['eng.1', 'esp.1', 'ita.1', 'ger.1', 'fra.1', 'egy.1', 'uefa.champions']:
    sb = get(f'{B}/{lg}/scoreboard?dates=20261030-20261105&limit=100')
    for e in sb.get('events', []):
        print('NEXT', lg, e['date'][:16], e['name'], e['id'])
    out[lg + ':next'] = [{'id': e['id'], 'date': e['date'], 'name': e['name']} for e in sb.get('events', [])]
json.dump(out, open('sample/yt/data.json', 'w'), ensure_ascii=False, indent=1)
