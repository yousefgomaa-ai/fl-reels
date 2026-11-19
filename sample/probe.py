# One-off (2026-11-19): Friday 20 November's fixtures reel for FB Legends, out at 3am Cairo (01:00 UTC), after #708's deploy.
import json, os, time, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
time.sleep(120)
for k in range(3):
    u = 'https://api.football-legend.com/v2/fben/dry?' + urllib.parse.urlencode({'key': K, 'kinds': 'none', 'special': 'day-2026-11-20', 'postat': '2026-11-20T01:00:00Z'})
    try: r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'fl-probe'}), timeout=150).read().decode()
    except Exception as e: r = 'error ' + str(e)
    print('PROBE', r[:500])
    if 'en-special-day-2026-11-20-1' in r: break
    time.sleep(90)
