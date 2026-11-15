# One-off (2026-11-15): why the English full-time reel of the Nations League 19:45 UK group is not made (a dry run, no writes).
import json, os, urllib.parse, urllib.request
k = urllib.parse.quote(os.environ.get('REELS_KEY', ''), safe='')
u = f'https://api.football-legend.com/v2/fben/dry?key={k}&kinds=none&state=en-ft-uefanations-20261115-1950'
j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (FootballLegends probe)'}), timeout=120))
print('PROBE state:', json.dumps(j.get('result',{}).get('state')))
for m in (j.get('result',{}).get('list') or []): print('PROBE list', m)
for d in (j.get('jobs') or []): print('PROBE dry', d.get('id'), '|', d.get('title'))
