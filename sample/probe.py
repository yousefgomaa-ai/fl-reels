# One-off (2026-11-03): /v2/ytv/status kept on the branch (sample/pl is committed by the next step).
import json, os, urllib.parse, urllib.request
k = urllib.parse.quote(os.environ['REELS_KEY'], safe='')
b = urllib.request.urlopen(urllib.request.Request(f'https://api.football-legend.com/v2/ytv/status?key={k}', headers={'User-Agent': 'fl-probe'}), timeout=180).read()
os.makedirs('sample/pl', exist_ok=True)
open('sample/pl/ytv-status.json', 'wb').write(b)
print(len(b))
