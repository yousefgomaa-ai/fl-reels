# Facts and pictures for the «مسار اللاعب» videos (owner, 2026-10-28): each line of sample/players.txt is
# "search name|commons search". FotMob's career (clubs, seasons, trophies) and logos, and Commons photo candidates.
import json, os, re, urllib.parse, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0; football-legend.com)'}
def get(u, raw=False):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
    return r if raw else json.loads(r)
os.makedirs('sample/pl', exist_ok=True)
for line in open('sample/players.txt'):
    if '|' not in line: continue
    name, cs = [x.strip() for x in line.split('|', 1)]
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    try:
        s = get('https://www.fotmob.com/api/data/search/suggest?term=' + urllib.parse.quote(name) + '&lang=en')
        pid = None
        for grp in s if isinstance(s, list) else [s]:
            for sug in (grp.get('suggestions') or []):
                if sug.get('type') == 'player': pid = sug.get('id'); break
            if pid: break
        print(name, 'fotmob id', pid)
        d = get(f'https://www.fotmob.com/api/data/playerData?id={pid}')
        keep = {k: d.get(k) for k in ('id', 'name', 'birthDate', 'primaryTeam', 'careerHistory', 'trophies', 'playerInformation', 'mainLeague')}
        json.dump(keep, open(f'sample/pl/{slug}.json', 'w'), ensure_ascii=False, indent=1)
        ids = set()
        for grp in (d.get('careerHistory') or {}).get('careerItems', {}).values():
            for e in grp.get('teamEntries') or []:
                ids.add(str(e.get('teamId')))
                print('  ', e.get('team'), e.get('startDate'), e.get('endDate'), 'apps', e.get('appearances'), 'g', e.get('goals'), 'a', e.get('assists'))
        for t in ids:
            f = f'sample/logo-{t}.png'
            if not os.path.exists(f):
                try: open(f, 'wb').write(get(f'https://images.fotmob.com/image_resources/logo/teamlogo/{t}.png', True))
                except Exception as e: print('logo', t, e)
    except Exception as e:
        print(name, 'fotmob failed', e)
    try:
        q = get('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', 'generator': 'search',
            'gsrsearch': cs + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 8, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size', 'iiurlwidth': 600}))
        meta = []
        for i, p in enumerate(sorted((q.get('query') or {}).get('pages', {}).values(), key=lambda x: x.get('index', 0))):
            ii = p['imageinfo'][0]; em = ii.get('extmetadata', {})
            f = f'sample/pl/{slug}-c{i}.jpg'
            open(f, 'wb').write(get(ii['thumburl'], True))
            meta.append({'n': i, 'title': p['title'], 'w': ii.get('width'), 'h': ii.get('height'), 'artist': re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', '')), 'license': em.get('LicenseShortName', {}).get('value', '')})
        json.dump(meta, open(f'sample/pl/{slug}-photos.json', 'w'), ensure_ascii=False, indent=1)
        print('  photos', len(meta))
    except Exception as e:
        print(name, 'commons failed', e)
