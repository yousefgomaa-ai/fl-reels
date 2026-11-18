# One-off (2026-11-18): the international break of 12-17 Nov 2026: every goal (ESPN), and the six leagues' top scorers
# (ESPN, then FotMob), to find which league stars scored for their country. Read-only, public feeds.
import json, urllib.request, datetime
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36'}
def get(u):
    try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40))
    except Exception as e: return {'error': str(e)}
# 1. top scorers of each league (FotMob league stats)
FM = {'eng.1': 47, 'esp.1': 87, 'ita.1': 55, 'ger.1': 54, 'fra.1': 53, 'tur.1': 71}
for lg, fid in FM.items():
    d = get(f'https://www.fotmob.com/api/data/leagues?id={fid}')
    st = (d.get('stats') or {}).get('players') or []
    top = next((x for x in st if x.get('header') in ('Top scorer', 'Goals') or x.get('name') == 'goals'), st[0] if st else None)
    rows = (top or {}).get('topThree') or []
    url = (top or {}).get('fetchAllUrl')
    allr = get(url) if url else {}
    lst = ((allr.get('TopLists') or [{}])[0].get('StatList') or [])[:15]
    print('PROBE top', lg, json.dumps([[r.get('ParticipantName'), r.get('TeamName'), r.get('StatValue'), r.get('MatchesPlayed')] for r in lst], ensure_ascii=False) if lst else json.dumps(rows, ensure_ascii=False)[:600])
# 2. every goal of the window, all ESPN national competitions
COMPS = ['uefa.nations', 'fifa.friendly', 'fifa.worldq.uefa', 'caf.nations_qual', 'fifa.worldq.caf', 'conmebol.america', 'concacaf.nations.league', 'afc.asian.cup.qual', 'fifa.worldq.conmebol']
for day in ['20261112', '20261113', '20261114', '20261115', '20261116', '20261117']:
    for c in COMPS:
        d = get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{c}/scoreboard?dates={day}')
        for ev in d.get('events', []) or []:
            co = (ev.get('competitions') or [{}])[0]
            t = {x['homeAway']: x for x in co.get('competitors', [])}
            h, a = t.get('home', {}), t.get('away', {})
            goals = []
            for g in co.get('details', []) or []:
                if not g.get('scoringPlay'): continue
                who = ', '.join(p.get('displayName', '') for p in g.get('athletesInvolved', []) or [])
                tag = ' (pen)' if g.get('penaltyKick') else ' (og)' if g.get('ownGoal') else ''
                goals.append(f"{g.get('clock', {}).get('displayValue', '')} {who}{tag} [{g.get('team', {}).get('displayName', '')}]")
            print('PROBE match', day, c, f"{h.get('team', {}).get('displayName')} {h.get('score')}-{a.get('score')} {a.get('team', {}).get('displayName')}", co.get('status', {}).get('type', {}).get('name'), '|', '; '.join(goals))
