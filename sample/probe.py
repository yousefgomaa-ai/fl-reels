# One-off (2026-11-03): is the API's latest code live? (/v2/ytv/status is new; /v2/ytv/jobs is old.)
import json, os, urllib.parse, urllib.request
k = urllib.parse.quote(os.environ['REELS_KEY'], safe='')
for p in ('/v2/ytv/jobs', '/v2/ytv/status', '/v2/reels/status'):
    try:
        r = urllib.request.urlopen(urllib.request.Request(f'https://api.football-legend.com{p}?key={k}', headers={'User-Agent': 'fl-probe'}), timeout=120)
        b = r.read().decode()
        print('CODE', p, r.status, len(b)); print(b[:6000] if p == '/v2/ytv/status' else b[:300])
    except Exception as e: print('CODE', p, e)
