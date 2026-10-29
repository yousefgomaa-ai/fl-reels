# Candidate photos per star for picking by eye (owner, 2026-10-29: more licensed photos in the star reels).
# From the player's Commons category (Wikidata P373) and its sub-categories two levels down: free JPEGs (CC BY, CC BY-SA,
# CC0, public domain) at least 800px on each side whose file name carries his name. Up to 9 per star, newest first, one
# a day of shooting; a numbered contact sheet and a manifest with each file's author and licence.
import json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from PIL import Image, ImageDraw
UA = {'User-Agent': 'FootballLegendsBot/1.0 (https://football-legend.com/about)'}
def get(url, **q):
    # Wikidata answers an error object (no 'search') when asked too fast: a pause between calls and a few tries.
    for t in range(5):
        time.sleep(0.4 + t * 3)
        try:
            with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(q), headers=UA), timeout=25) as r:
                d = json.load(r)
            if 'error' not in d: return d
            print('  ! api', d['error'].get('code'))
        except Exception as e: print('  ! get', e)
    return {}
LIC = re.compile(r"^(CC BY(-SA)? \d(\.\d)?|CC0( 1\.0)?|Public domain)$", re.I)
txt = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()
fold = lambda s: unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
def members(cat, kind):
    q = dict(action='query', format='json', generator='categorymembers', gcmtitle='Category:' + cat, gcmtype=kind, gcmlimit='200')
    if kind == 'file': q.update(prop='imageinfo', iiprop='url|size|mime|extmetadata', iiurlwidth='300', iiextmetadatafilter='LicenseShortName|Artist|DateTimeOriginal')
    try: return list(get('https://commons.wikimedia.org/w/api.php', **q).get('query', {}).get('pages', {}).values())
    except Exception as e: print('  !', cat, e); return []
def item_of(name, cit):
    ids = [x['id'] for x in get('https://www.wikidata.org/w/api.php', action='wbsearchentities', search=name, language='en', type='item', limit=6, format='json').get('search', [])]
    if not ids: return None
    ents = get('https://www.wikidata.org/w/api.php', action='wbgetentities', ids='|'.join(ids), props='claims', format='json').get('entities', {})
    if not ents: return None
    for i in ids:
        c = ents.get(i, {}).get('claims', {}); v = lambda p: [x['mainsnak'].get('datavalue', {}).get('value') for x in c.get(p, [])]
        if cit and not any(isinstance(x, dict) and x.get('id') == cit for x in v('P27')): continue
        if any(isinstance(x, dict) and x.get('id') == 'Q937857' for x in v('P106')): return dict(img=(v('P18') or [''])[0], cat=(v('P373') or [None])[0])
    return None
os.makedirs('probe/out', exist_ok=True)
manifest = {}
for line in open('probe/stars.txt', encoding='utf-8'):
    slug, name, cit = (line.strip().split('|') + ['', ''])[:3]
    if not slug: continue
    item = item_of(name, cit)
    print('==', slug, item)
    if not item or not item['cat']: continue
    keys = [w for w in fold(name).replace('-', ' ').split() if len(w) >= 4] or [fold(name)]
    cats, pages = [item['cat']], []
    for depth in range(2):
        nxt = []
        for c in cats:
            pages += members(c, 'file')
            subs = [p['title'][9:] for p in members(c, 'subcat')]
            nxt += sorted(subs, key=lambda t: (re.search(r"(?:19|20)\d{2}", t) or re.search('', '')).group(0) or '0', reverse=True)[:4]
        cats = nxt
    pages += [pg for c in cats for pg in members(c, 'file')]
    seen, cand = set(), []
    for pg in pages:
        f = pg['title'][5:]
        if f in seen: continue
        seen.add(f)
        ii = (pg.get('imageinfo') or [None])[0]
        if not ii or ii.get('mime') != 'image/jpeg' or ii['width'] < 800 or ii['height'] < 800 or not ii.get('thumburl'): continue
        if not any(k in fold(f) for k in keys): continue
        md = ii.get('extmetadata', {}); lic = txt(md.get('LicenseShortName', {}).get('value')); art = txt(md.get('Artist', {}).get('value'))[:60]
        if not LIC.match(lic) or not art: continue
        d = re.search(r"(\d{4})[-:](\d{2})[-:](\d{2})", txt(md.get('DateTimeOriginal', {}).get('value'))) or re.search(r"\b((?:19|20)\d{2})\b", f)
        cand.append(dict(file=f, thumb=ii['thumburl'], credit=f"{art} ({lic})", day='-'.join(d.groups()) if d else '', w=ii['width'], h=ii['height']))
    cand.sort(key=lambda x: x['day'], reverse=True)
    out, days = [], set()
    for x in cand:
        if len(out) >= 9: break
        if x['day'] and x['day'] in days: continue
        out.append(x); days.add(x['day'])
    print('  candidates', len(cand), 'kept', len(out))
    if not out: continue
    sheet = Image.new('RGB', (900, 300 * ((len(out) + 2) // 3)), 'black'); dr = ImageDraw.Draw(sheet)
    for i, x in enumerate(out):
        try:
            with urllib.request.urlopen(urllib.request.Request(x['thumb'], headers=UA), timeout=25) as r: im = Image.open(r).convert('RGB')
            im.thumbnail((296, 296)); sheet.paste(im, ((i % 3) * 300 + 2, (i // 3) * 300 + 2))
        except Exception as e: print('  ! thumb', e)
        dr.rectangle([(i % 3) * 300, (i // 3) * 300, (i % 3) * 300 + 34, (i // 3) * 300 + 30], fill='yellow'); dr.text(((i % 3) * 300 + 8, (i // 3) * 300 + 8), str(i + 1), fill='black')
    sheet.save(f'probe/out/{slug}.jpg', quality=70)
    manifest[slug] = [{k: x[k] for k in ('file', 'credit', 'day', 'w', 'h')} for x in out]
json.dump(manifest, open('probe/out/manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
