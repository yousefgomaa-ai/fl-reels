# One-off (2026-11-03): after the round-summary fix, watches /v2/ytv/status for the missing leagues' jobs.
import json, os, time, urllib.parse, urllib.request
k = urllib.parse.quote(os.environ['REELS_KEY'], safe='')
os.makedirs('sample/pl', exist_ok=True)
for t in range(13):
    try:
        b = urllib.request.urlopen(urllib.request.Request(f'https://api.football-legend.com/v2/ytv/status?key={k}', headers={'User-Agent': 'fl-probe'}), timeout=180).read()
        open('sample/pl/ytv-status.json', 'wb').write(b)
        d = json.loads(b); ids = [j['id'] for j in d['jobs']]
        print(time.strftime('%H:%M'), ids)
        if any('ita1' in i for i in ids) and any('ger1' in i for i in ids): break
    except Exception as e: print('err', e)
    time.sleep(60)
