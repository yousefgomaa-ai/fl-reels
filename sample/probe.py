# One-off (2026-11-18): the owner's comedy reel queued for FB Legends at noon Cairo (10:00 UTC), after the deploy of #703.
import json, os, time, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
time.sleep(120)
for k in range(3):
    u = 'https://api.football-legend.com/v2/fben/dry?' + urllib.parse.urlencode({'key': K, 'kinds': 'none', 'ownvideo': 'comedy-sub', 'postat': '2026-11-18T10:00:00Z'})
    try: r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'fl-probe'}), timeout=120).read().decode()
    except Exception as e: r = 'error ' + str(e)
    print('PROBE', r[:500])
    if '"ownvideo"' in r: break
    time.sleep(90)
