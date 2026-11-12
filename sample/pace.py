# One-off probe (owner, 2026-11-12): once the API is deployed, queue the eleven new specials (music only), and a live check.
import json, os, time, urllib.request
K = os.environ['REELS_KEY']; A = 'https://api.football-legend.com'
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=150) as r: return r.status, r.read().decode()[:400]
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:300]
    except Exception as e: return 0, str(e)
time.sleep(360)
for p in ['/club/status', '/v2/hero']: print('LIVE', p, get(A + p)[0], flush=True)
print('SITE', get('https://football-legend.com/')[0], flush=True)
for n in ['pace-pl', 'pace-laliga', 'pace-bund', 'pace-seriea', 'pace-l1', 'alltime-pl', 'alltime-laliga', 'alltime-seriea', 'alltime-bund', 'alltime-l1', 'alltime-ucl']:
    st, b = get(f'{A}/v2/fben/dry?key={K}&kinds=none&novoice=1&special={n}')
    print('Q', n, st, b.replace(K, '***')[:300], flush=True)
