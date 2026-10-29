# One-off look at how the sources carry a penalty shootout (owner, 2026-10-29: shootouts missing on the cards).
import json, urllib.request
UA = {'User-Agent': 'Mozilla/5.0'}
get = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())
for day in ('20261028', '20261029'):
    d = get('https://www.fotmob.com/api/data/matches?date=' + day)
    for l in d.get('leagues') or []:
        for m in l.get('matches') or []:
            st = m.get('status') or {}
            r = json.dumps(st.get('reason') or {})
            if 'en' in r.lower() and ('pen' in r.lower()):
                print('FM', day, l.get('name'), m.get('id'), m['home'].get('name'), m['home'].get('score'), m['away'].get('name'), m['away'].get('score'))
                print('   status', json.dumps(st)[:600])
                print('   home', json.dumps(m['home'])[:300])
                mid = m.get('id')
    for slug in ('eng.league_cup', 'esp.copa_del_rey', 'ger.dfb_pokal'):
        try:
            s = get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={day}')
            for e in s.get('events') or []:
                c = e['competitions'][0]
                if any('shootoutScore' in x for x in c['competitors']):
                    print('ESPN', day, slug, e['id'], e['name'], [(x['team']['displayName'], x.get('score'), x.get('shootoutScore'), x.get('winner')) for x in c['competitors']], json.dumps(c.get('status', {}).get('type', {}))[:300])
        except Exception as ex: print('ESPN', slug, ex)
try:
    md = get(f'https://www.fotmob.com/api/data/matchDetails?matchId={mid}')
    h = md.get('header', {})
    print('MD header status', json.dumps(h.get('status'))[:1200])
    print('MD teams', json.dumps(h.get('teams'))[:500])
except Exception as ex: print('md', ex)
