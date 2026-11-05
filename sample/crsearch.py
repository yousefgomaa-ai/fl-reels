# One-off: Commons photos of Cristiano Ronaldo in the Portugal shirt, by year (FB Legends farewell reel, 2026-11-05).
import json, urllib.request, urllib.parse, os, re, time
UA = {'User-Agent': 'FBLegendsReels/1.0 (football-legend.com)'}
def api(**q):
    q.update(format='json'); u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(q)
    for i in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40))
        except Exception as e: time.sleep(3 + i * 3)
    return {}
files = {}
for cat in ['Category:Cristiano Ronaldo with the Portugal national football team', 'Category:Cristiano Ronaldo in 2004', 'Category:Cristiano Ronaldo in 2006', 'Category:Cristiano Ronaldo in 2008',
            'Category:Cristiano Ronaldo in 2012', 'Category:Cristiano Ronaldo in 2014', 'Category:Cristiano Ronaldo in 2016', 'Category:Cristiano Ronaldo in 2018', 'Category:Cristiano Ronaldo in 2022', 'Category:Cristiano Ronaldo in 2024', 'Category:Cristiano Ronaldo in 2025', 'Category:Cristiano Ronaldo in 2026', 'Category:Cristiano Ronaldo']:
    d = api(action='query', list='categorymembers', cmtitle=cat, cmlimit='300', cmtype='file|subcat')
    m = d.get('query', {}).get('categorymembers', [])
    print(cat, len(m), [x['title'] for x in m if x['title'].startswith('Category:')][:40])
    for x in m:
        if x['title'].startswith('File:'): files[x['title']] = cat
for s in ['Cristiano Ronaldo Portugal 2003', 'Cristiano Ronaldo Euro 2004', 'Cristiano Ronaldo Portugal 2006 World Cup', 'Cristiano Ronaldo Portugal Euro 2016', 'Cristiano Ronaldo Portugal 2018', 'Cristiano Ronaldo Portugal captain', 'Ronaldo Portugal national team']:
    d = api(action='query', list='search', srsearch=s, srnamespace='6', srlimit='40')
    for x in d.get('query', {}).get('search', []): files.setdefault(x['title'], 'search:' + s)
print('files', len(files))
titles = list(files); info = {}
for i in range(0, len(titles), 40):
    d = api(action='query', titles='|'.join(titles[i:i+40]), prop='imageinfo', iiprop='url|size|extmetadata', iiurlwidth='480')
    for p in d.get('query', {}).get('pages', {}).values():
        ii = (p.get('imageinfo') or [{}])[0]; md = ii.get('extmetadata', {})
        g = lambda k: re.sub('<[^>]+>', '', (md.get(k) or {}).get('value', ''))[:120]
        info[p['title']] = dict(w=ii.get('width'), h=ii.get('height'), thumb=ii.get('thumburl'), date=g('DateTimeOriginal') or g('DateTime'), lic=g('LicenseShortName'), artist=g('Artist'), desc=g('ImageDescription'), cat=files.get(p['title']))
json.dump(info, open('look/cr_files.json', 'w'), indent=1, ensure_ascii=False)
os.makedirs('look/cr', exist_ok=True)
keep = [t for t, v in info.items() if v['thumb'] and re.search(r'portugal|seleç|selec|euro|world cup|copa|wc|nations|national|por\b|fpf|2004|2006|2016', (t + ' ' + v['desc'] + ' ' + (v['cat'] or '')).lower())]
print('keep', len(keep))
for n, t in enumerate(keep[:80]):
    try:
        b = urllib.request.urlopen(urllib.request.Request(info[t]['thumb'], headers=UA), timeout=40).read()
        open(f'look/cr/{n:02d}.jpg', 'wb').write(b); info[t]['n'] = n
    except Exception as e: print('x', t, e)
    time.sleep(0.4)
json.dump({t: info[t] for t in keep}, open('look/cr_keep.json', 'w'), indent=1, ensure_ascii=False)
