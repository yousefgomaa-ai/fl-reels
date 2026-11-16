# One-off (2026-11-16): the starting XIs of Spain v England (15 Nov) with each player's ESPN position and formation place.
import json, urllib.request
H = {'User-Agent': 'Mozilla/5.0'}
sb = json.load(urllib.request.urlopen(urllib.request.Request('https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.nations/scoreboard?dates=20261115&limit=100', headers=H), timeout=30))
for e in sb['events']:
    if 'England' not in e['name'] and 'Italy' not in e['name']: continue
    s = json.load(urllib.request.urlopen(urllib.request.Request(f"https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.nations/summary?event={e['id']}", headers=H), timeout=30))
    for r in s.get('rosters', []):
        print('PROBE', e['name'], '|', r['team']['displayName'], r.get('formation'))
        for p in r.get('roster', []):
            if p.get('starter'): print('PROBE  ', p.get('formationPlace'), p.get('jersey'), (p.get('position') or {}).get('abbreviation'), p['athlete']['displayName'])
