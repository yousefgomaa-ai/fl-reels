# One-off (2026-11-18): «BACK ON FIRE» queued for FB Legends (&special=break-stars, after #707's deploy); asked on Telegram.
import json, os, time, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
time.sleep(120)
for k in range(3):
    u = 'https://api.football-legend.com/v2/fben/dry?' + urllib.parse.urlencode({'key': K, 'kinds': 'none', 'special': 'break-stars'})
    try: r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'fl-probe'}), timeout=120).read().decode()
    except Exception as e: r = 'error ' + str(e)
    print('PROBE', r[:400])
    if 'en-special-break-stars-1' in r: break
    time.sleep(90)
