# The photos shown behind a career video's scenes (owner, 2026-10-28: "اكتر من صوره للاعب"), from Wikimedia Commons at
# 1080 px, each with its author and licence for the credit line.
import json, os, re, time, urllib.parse, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0; football-legend.com)'}
os.makedirs('sample/ph', exist_ok=True)
out = []
for i, t in enumerate([x.strip() for x in open('sample/photos.txt') if x.strip()]):
    time.sleep(3)
    try:
        q = json.loads(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json',
            'titles': t, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata', 'iiurlwidth': 1080}), headers=UA), timeout=30).read())
        ii = list(q['query']['pages'].values())[0]['imageinfo'][0]; em = ii.get('extmetadata', {})
        time.sleep(2)
        open(f'sample/ph/{i:02d}.jpg', 'wb').write(urllib.request.urlopen(urllib.request.Request(ii['thumburl'], headers=UA), timeout=60).read())
        out.append({'n': i, 'title': t, 'artist': re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', '')).strip(), 'license': em.get('LicenseShortName', {}).get('value', '')})
        print(i, out[-1])
    except Exception as e:
        print(i, t, 'failed', e)
json.dump(out, open('sample/ph/credits.json', 'w'), ensure_ascii=False, indent=1)
