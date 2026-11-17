# One-off (2026-11-17): the Bundesliga November fixtures made again, now that the old job is really dropped (#702).
import json, os, time, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
time.sleep(150)  # Cloudflare's build of the merge
u = 'https://api.football-legend.com/v2/fben/dry?' + urllib.parse.urlencode({'key': K, 'kinds': 'none', 'special': 'month-ger.1'})
try: print('PROBE', urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'fl-probe'}), timeout=120).read().decode()[:600])
except Exception as e: print('PROBE error', e)
