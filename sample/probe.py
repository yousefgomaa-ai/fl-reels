# One-off probe (owner, 2026-11-14): ESPN crests for the trend reel sample. claude/nla-probe only.
import json, urllib.request
H = {'User-Agent': 'FBLegendsBot/1.0'}
want = ['Liverpool', 'Brentford', 'Newcastle United', 'Sporting CP', 'Manchester United', 'Espanyol', 'Southampton', 'Tottenham Hotspur', 'Paris Saint-Germain', 'Chelsea']
for lg in ['eng.1', 'eng.2', 'esp.1', 'esp.2', 'fra.1', 'por.1']:
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/teams', headers=H), timeout=60))
        for t in d['sports'][0]['leagues'][0]['teams']:
            t = t['team']
            if t['displayName'] in want: print('T', lg, t['id'], t['displayName'], (t.get('logos') or [{}])[0].get('href', ''))
    except Exception as e: print('fail', lg, e)
