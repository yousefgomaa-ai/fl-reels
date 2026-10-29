# Which free Commons photos a player's category offers (a check of the filter: CC BY / BY-SA / CC0 / PD JPEGs >= 800px,
# no group shots by name, newest first, one a day). Prints the picks for a few players.
import json, re, sys, urllib.parse, urllib.request
UA = {'User-Agent': 'FootballLegendsBot/1.0 (https://football-legend.com/about)'}
def get(url, **q):
    with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(q), headers=UA), timeout=20) as r:
        return json.load(r)
OTHERS = re.compile(r"(\b(and|with|und|y|et|e|team|squad|line-?up|fans|supporters|stadium|signature|autograph|mural|statue|wax|graffiti|poster|parade|family|wife)\b|&)", re.I)
LIC = re.compile(r"^(CC BY(-SA)? \d(\.\d)?|CC0( 1\.0)?|Public domain)$", re.I)
txt = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()
def files(cat, kind='file'):
    q = dict(action='query', format='json', generator='categorymembers', gcmtitle='Category:' + cat, gcmtype=kind, gcmlimit='100')
    if kind == 'file': q.update(prop='imageinfo', iiprop='url|size|mime|extmetadata', iiurlwidth='720', iiextmetadatafilter='LicenseShortName|Artist|DateTimeOriginal')
    return list(get('https://commons.wikimedia.org/w/api.php', **q).get('query', {}).get('pages', {}).values())
def photo(pg):
    ii = (pg.get('imageinfo') or [None])[0]; f = pg['title'][5:]
    if not ii or ii.get('mime') != 'image/jpeg' or ii['width'] < 800 or ii['height'] < 800 or not ii.get('thumburl'): return None
    if OTHERS.search(re.sub(r"[_,()-]", " ", re.sub(r"\.[a-z]+$", "", f, flags=re.I))): return None
    md = ii.get('extmetadata', {}); lic = txt(md.get('LicenseShortName', {}).get('value')); art = txt(md.get('Artist', {}).get('value'))[:60]
    if not LIC.match(lic) or not art: return None
    d = re.search(r"(\d{4})[-:](\d{2})[-:](\d{2})", txt(md.get('DateTimeOriginal', {}).get('value'))) or re.search(r"\b((?:19|20)\d{2})\b", f)
    return dict(file=f, url=ii['thumburl'], credit=f"{art} ({lic})", day='-'.join(d.groups()) if d else '')
def year(t):
    m = re.search(r"(?:19|20)\d{2}", t); return m.group(0) if m else '0'
for name in sys.argv[1:]:
    ids = [x['id'] for x in get('https://www.wikidata.org/w/api.php', action='wbsearchentities', search=name, language='en', type='item', limit=6, format='json')['search']]
    ents = get('https://www.wikidata.org/w/api.php', action='wbgetentities', ids='|'.join(ids), props='claims', format='json')['entities']
    item = None
    for i in ids:
        c = ents[i].get('claims', {}); v = lambda p: [x['mainsnak'].get('datavalue', {}).get('value') for x in c.get(p, [])]
        if any(isinstance(x, dict) and x.get('id') == 'Q937857' for x in v('P106')) and v('P18'): item = dict(img=v('P18')[0], cat=(v('P373') or [None])[0]); break
    print('==', name, item)
    if not item or not item['cat']: continue
    pages = files(item['cat']); direct = len([p for p in pages if photo(p)])
    subs = []
    if direct < 6:
        subs = sorted([p['title'][9:] for p in files(item['cat'], 'subcat') if not OTHERS.search(re.sub(r"^.*?\b(?:in|at)\b", "", p['title'][9:], flags=re.I))], key=year, reverse=True)[:3]
        for s in subs: pages += files(s)
    allp = sorted([x for x in map(photo, pages) if x], key=lambda x: x['day'], reverse=True)
    print('  direct ok:', direct, 'subs:', subs, 'candidates:', len(allp))
    out, days = [], set()
    p18 = next((x for x in allp if x['file'].replace('_', ' ') == item['img'].replace('_', ' ')), None)
    if p18: out.append(p18); days.add(p18['day'])
    for x in allp:
        if len(out) >= 3: break
        if x in out or (x['day'] and x['day'] in days): continue
        out.append(x); days.add(x['day'])
    for x in out: print('  ', x['day'], '|', x['file'], '|', x['credit'])
