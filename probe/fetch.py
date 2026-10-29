# The picked photos (probe/picks.json): each file's licence and author from Commons, the 960px copy the site's reel frame
# asks for (Special:FilePath?width=960) with its byte size (the frame takes up to 600 KB), and a numbered sheet per star.
# Also Salah's category without the name filter (his photos are named after the matches, not him).
import json, os, re, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw
UA = {'User-Agent': 'FootballLegendsBot/1.0 (https://football-legend.com/about)'}
LIC = re.compile(r"^(CC BY(-SA)? \d(\.\d)?|CC0( 1\.0)?|Public domain)$", re.I)
txt = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()
def get(url, **q):
    for t in range(5):
        time.sleep(0.3 + t * 3)
        try:
            with urllib.request.urlopen(urllib.request.Request(url + ('?' + urllib.parse.urlencode(q) if q else ''), headers=UA), timeout=30) as r: b = r.read()
            return json.loads(b) if q else b
        except Exception as e: print('  ! get', e)
    return {} if q else b''
def info(f):
    p = list(get('https://commons.wikimedia.org/w/api.php', action='query', format='json', titles='File:' + f, prop='imageinfo', iiprop='size|mime|extmetadata',
        iiextmetadatafilter='LicenseShortName|Artist|DateTimeOriginal').get('query', {}).get('pages', {}).values())
    ii = (p[0].get('imageinfo') or [{}])[0] if p else {}
    md = ii.get('extmetadata', {})
    return dict(lic=txt(md.get('LicenseShortName', {}).get('value')), artist=txt(md.get('Artist', {}).get('value'))[:60], w=ii.get('width'), h=ii.get('height'), mime=ii.get('mime'))
def sheet(name, files):
    ims = []
    for i, f in enumerate(files, 1):
        b = get('https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(f.replace(' ', '_')) + '?width=330')
        try:
            import io; im = Image.open(io.BytesIO(b)).convert('RGB'); im.thumbnail((296, 296)); ims.append(im)
        except Exception: ims.append(Image.new('RGB', (296, 296), 'gray'))
    s = Image.new('RGB', (900, 300 * ((len(ims) + 2) // 3)), 'black'); d = ImageDraw.Draw(s)
    for i, im in enumerate(ims):
        x, y = (i % 3) * 300, (i // 3) * 300; s.paste(im, (x + 2, y + 2)); d.rectangle([x, y, x + 34, y + 30], fill='yellow'); d.text((x + 8, y + 8), str(i + 1), fill='black')
    s.save(f'probe/check/{name}.jpg', quality=70)
os.makedirs('probe/check', exist_ok=True)
picks, report = json.load(open('probe/picks.json', encoding='utf-8')), {}
for slug, files in picks.items():
    report[slug] = []
    for f in files:
        i = info(f)
        b = get('https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(f.replace(' ', '_')) + '?width=960')
        i.update(file=f, bytes=len(b), ok=bool(LIC.match(i['lic'] or '')) and bool(i['artist']) and 0 < len(b) <= 600000)
        report[slug].append(i)
        print(slug, '|', 'OK ' if i['ok'] else 'BAD', i['bytes'], i['lic'], '|', i['artist'], '|', f)
    if files: sheet(slug, files)
# Salah's category, newest first, no name filter.
pages = list(get('https://commons.wikimedia.org/w/api.php', action='query', format='json', generator='categorymembers', gcmtitle='Category:Mohamed Salah', gcmtype='file', gcmlimit='200',
    prop='imageinfo', iiprop='size|mime|extmetadata', iiextmetadatafilter='LicenseShortName|Artist|DateTimeOriginal').get('query', {}).get('pages', {}).values())
cand = []
for p in pages:
    ii = (p.get('imageinfo') or [{}])[0]; md = ii.get('extmetadata', {})
    if ii.get('mime') != 'image/jpeg' or (ii.get('width') or 0) < 800 or (ii.get('height') or 0) < 800 or not LIC.match(txt(md.get('LicenseShortName', {}).get('value'))): continue
    d = re.search(r"(\d{4})[-:](\d{2})[-:](\d{2})", txt(md.get('DateTimeOriginal', {}).get('value')))
    cand.append((d.group(0) if d else '', p['title'][5:], txt(md.get('Artist', {}).get('value'))[:60] + ' (' + txt(md.get('LicenseShortName', {}).get('value')) + ')'))
cand.sort(reverse=True); cand = cand[:15]
for i, c in enumerate(cand, 1): print('salah-all', i, c[0], '|', c[1], '|', c[2])
sheet('salah-all', [c[1] for c in cand])
report['salah-all'] = [dict(file=c[1], credit=c[2], day=c[0]) for c in cand]
json.dump(report, open('probe/check/report.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
