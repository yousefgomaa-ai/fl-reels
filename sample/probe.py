# One-off live check after the Romano PR (#454) merge on the site repo, 2026-10-30. Deleted after reading.
import json, urllib.request, time
def get(u):
    t = time.time()
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'fl-probe'}), timeout=40)
        b = r.read(); return r.status, r.headers.get('Content-Type'), len(b), b, round(time.time() - t, 1)
    except urllib.error.HTTPError as e:
        b = e.read(); return e.code, e.headers.get('Content-Type'), len(b), b, round(time.time() - t, 1)
    except Exception as e:
        return 'ERR', str(e), 0, b'', round(time.time() - t, 1)
A = 'https://api.football-legend.com'
for p in ['/club/status', '/status/sources', '/v2/hero', '/card.jpg?kind=follow', '/sitemap-matches.xml', '/v2/errors']:
    s, ct, n, b, dt = get(A + p)
    print(f'{s} {ct} {n}B {dt}s {p}')
    if p == '/v2/errors':
        txt = b.decode('utf8', 'replace')
        print('romano in errors:', 'romano' in txt)
        try:
            d = json.loads(txt)
            print(json.dumps({k: d[k] for k in list(d)[:6]}, ensure_ascii=False)[:1500])
        except Exception:
            print(txt[:600])
for u in ['https://football-legend.com/', 'https://football-legend.com/sitemap.xml']:
    s, ct, n, b, dt = get(u); print(f'{s} {n}B {dt}s {u}')
