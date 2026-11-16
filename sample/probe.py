# One-off (2026-11-16): FotMob's starting XIs for Spain v England, 5181860 (match 5181860): the fields each starter carries.
import json, urllib.request
r = urllib.request.urlopen(urllib.request.Request('https://www.fotmob.com/api/data/matchDetails?matchId=5181860', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'}), timeout=30)
d = json.load(r); lu = (d.get('content') or {}).get('lineup') or {}
print('PROBE keys', list(lu.keys())[:20])
for side in ('homeTeam', 'awayTeam'):
    t = lu.get(side) or {}
    print('PROBE', side, t.get('name'), t.get('formation'), 'keys:', list(t.keys())[:20])
    for p in (t.get('starters') or [])[:11]:
        print('PROBE  ', p.get('shirtNumber'), p.get('name'), 'pos', p.get('positionId'), 'usual', p.get('usualPlayingPositionId'), 'h', json.dumps(p.get('horizontalLayout')), 'v', json.dumps(p.get('verticalLayout')))
