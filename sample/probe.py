# One-off (2026-11-15): why the English full-time reel of the Nations League 19:45 UK group is not made (a dry run, no writes).
import json, os, urllib.parse, urllib.request
k = urllib.parse.quote(os.environ.get('REELS_KEY', ''), safe='')
u = f'https://api.football-legend.com/v2/fben/dry?key={k}&kinds=live&list=1&at=2026-11-15T21:50:00Z'
j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (FootballLegends probe)'}), timeout=120))
print('PROBE live:', j.get('result',{}).get('live'))
for m in (j.get('result',{}).get('list') or []): print('PROBE list', m)
for d in (j.get('jobs') or []): print('PROBE dry', d.get('id'), '|', d.get('title'))
