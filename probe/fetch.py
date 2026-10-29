# The picked photos at the size the site's reel frame asks Commons for (Special:FilePath, 720px), with their byte size:
# the frame takes images up to 350 KB.
import os, urllib.parse, urllib.request, time
UA = {'User-Agent': 'FootballLegendsBot/1.0 (https://football-legend.com/about)'}
os.makedirs('probe/full', exist_ok=True)
for i, f in enumerate([l.strip() for l in open('probe/fetch.txt', encoding='utf-8') if l.strip()], 1):
    url = 'https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(f.replace(' ', '_')) + '?width=720'
    for t in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: b = r.read()
            break
        except Exception as e: print('  !', f, e); time.sleep(3 + t * 4); b = b''
    open(f'probe/full/{i:03d}.jpg', 'wb').write(b)
    print(f'{i:03d}', len(b), 'OVER' if len(b) > 350000 else 'ok', '|', f)
