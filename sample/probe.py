# One-off (2026-11-16): is the new relay live? A finished Nations League match the server has not read yet, through the
# API's live feed (FotMob path): its starters should now carry fx/fy (FotMob's pitch spots).
import json, urllib.request
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36'}
d = json.load(urllib.request.urlopen(urllib.request.Request('https://www.fotmob.com/api/data/matches?date=20261115', headers=H), timeout=30))
ids = []
for lg in d.get('leagues', []):
    if 'Nations League' not in str(lg.get('name')) and 'Nations League' not in str(lg.get('parentLeagueName')): continue
    for m in lg.get('matches', []):
        if m.get('status', {}).get('finished'): ids.append((m['id'], m['home']['name'], m['away']['name']))
print('PROBE finished UNL matches', len(ids))
skip = {'Spain', 'England', 'Belgium', 'Italy', 'France', 'Turkiye', 'Croatia', 'Czechia'}
for mid, h, a in [x for x in ids if x[1] not in skip and x[2] not in skip][:3]:
    try:
        j = json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.football-legend.com/match/live-feed?league=fra.coupe_de_france&eventId=fm-{mid}', headers=H), timeout=60))
        for l in j.get('lineups', []):
            st = [p for p in l.get('players', []) if p.get('starter')]
            print('PROBE', mid, h, 'v', a, l.get('side'), l.get('formation'), 'starters', len(st), 'with spots', sum(1 for p in st if p.get('fx') is not None), (st[1] if len(st) > 1 else None))
    except Exception as e:
        print('PROBE', mid, h, a, 'error', e)
