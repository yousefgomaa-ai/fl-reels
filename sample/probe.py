# One-off (2026-11-15): FB Legends' records for the Nations League groups tonight (read only).
import json, os, time, urllib.parse, urllib.request
time.sleep(150)  # Cloudflare's deploy of the read-only look
k = urllib.parse.quote(os.environ.get('REELS_KEY', ''), safe='')
u = f'https://api.football-legend.com/v2/fben/dry?key={k}&kinds=none&snap=natlive'
j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (FootballLegends probe)'}), timeout=120))
r = j.get('result', {})
print('PROBE snap', json.dumps(r.get('snap'))[:3000])
for m in r.get('marks') or []: print('PROBE mark', json.dumps(m)[:400])
