# Compares our API's day lists (11-30 Nov) with ESPN's schedules for the same competitions.
import json, os, re, sys, unicodedata, urllib.request, datetime
API = 'https://api.football-legend.com'
def get(u, t=90):
    req = urllib.request.Request(u, headers={'User-Agent': 'fl-check/1.0', 'Accept-Encoding': 'identity'})
    with urllib.request.urlopen(req, timeout=t) as r: return json.loads(r.read().decode('utf-8'))
def walk(o, out):
    if isinstance(o, dict):
        if 'fixture' in o and 'teams' in o and isinstance(o.get('teams'), dict): out.append(o)
        else:
            for v in o.values(): walk(v, out)
    elif isinstance(o, list):
        for v in o: walk(v, out)
STOP = {'fc','cf','sc','ac','afc','cd','club','de','the','sk','fk','sv','vfb','vfl','tsg','rc','rcd','ud','sd','ca','as','us','ss','ssc','1','04','05','09','calcio','city','united'}
def norm(n):
    n = unicodedata.normalize('NFKD', str(n or '')).encode('ascii', 'ignore').decode().lower()
    n = re.sub(r'[^a-z0-9 ]', ' ', n)
    return {w for w in n.split() if w not in STOP and len(w) > 1}
def same(a, b):
    A, B = norm(a), norm(b)
    return bool(A and B and (A & B))
ours = []
for d in range(11, 31):
    ds = f'202611{d:02d}'
    try: j = get(f'{API}/matches?date={ds}')
    except Exception as e: print('ERR ours', ds, e); continue
    ev = []; walk(j, ev)
    for e in ev:
        lg = e.get('leagueSlug') or (e.get('league') or {}).get('slug') or ''
        ours.append({'id': str(e.get('id')), 'lg': lg, 'date': e['fixture'].get('date'), 'h': e['teams']['home'].get('name'), 'a': e['teams']['away'].get('name'), 'day': ds})
# de-dup by id
seen = {}; 
for m in ours: seen.setdefault(m['id'], m)
ours = list(seen.values())
print('our matches 11-30 Nov:', len(ours))
leagues = sorted({m['lg'] for m in ours if m['lg']})
espn = {}
for lg in leagues:
    try:
        j = get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard?dates=20261101-20261210&limit=1000')
        L = []
        for e in j.get('events', []):
            c = e['competitions'][0]['competitors']
            h = [x for x in c if x['homeAway'] == 'home'][0]['team']['displayName']; a = [x for x in c if x['homeAway'] == 'away'][0]['team']['displayName']
            L.append({'date': e['date'], 'h': h, 'a': a, 'st': e.get('status', {}).get('type', {}).get('name', '')})
        espn[lg] = L
    except Exception as e: espn[lg] = None
def p(t): return datetime.datetime.fromisoformat(t.replace('Z', '+00:00'))
bad, missing_espn, nocover = [], [], []
for m in ours:
    L = espn.get(m['lg'])
    if L is None or not L: nocover.append(m); continue
    hit = [x for x in L if same(x['h'], m['h']) and same(x['a'], m['a'])] or [x for x in L if same(x['h'], m['a']) and same(x['a'], m['h'])]
    if not hit: missing_espn.append(m); continue
    best = min(hit, key=lambda x: abs((p(x['date']) - p(m['date'])).total_seconds()))
    diff = (p(best['date']) - p(m['date'])).total_seconds() / 3600
    if abs(diff) >= 0.5: bad.append((m, best, diff))
print('\n== DATE/TIME DIFFERENT FROM ESPN (ours -> espn):', len(bad))
for m, b, d in sorted(bad, key=lambda x: x[0]['date']):
    print(f"  {m['lg']:18} {m['id']:14} ours {m['date'][:16]}  espn {b['date'][:16]}  ({d:+.1f}h)  {m['h']} v {m['a']}  [espn: {b['h']} v {b['a']} {b['st']}]")
print('\n== NOT FOUND IN ESPN (league covered by ESPN):', len(missing_espn))
for m in sorted(missing_espn, key=lambda x: x['date']): print(f"  {m['lg']:18} {m['id']:14} {m['date'][:16]}  {m['h']} v {m['a']}")
print('\n== LEAGUE NOT ON ESPN (cannot cross-check):', len(nocover))
from collections import Counter
print('  ', dict(Counter(m['lg'] for m in nocover)))
for m in sorted(nocover, key=lambda x: x['date']):
    if not m['id'].startswith('fd-'): print(f"  {m['lg']:18} {m['id']:14} {m['date'][:16]}  {m['h']} v {m['a']}")
# twins: the same pairing twice in our lists
print('\n== SAME PAIR LISTED TWICE IN OUR DATA:')
for i, m in enumerate(ours):
    for k in ours[i+1:]:
        if m['lg'] == k['lg'] and ((same(m['h'], k['h']) and same(m['a'], k['a'])) or (same(m['h'], k['a']) and same(m['a'], k['h']))):
            print(f"  {m['lg']} {m['id']} {m['date'][:16]} | {k['id']} {k['date'][:16]}  {m['h']} v {m['a']}")
json.dump({'ours': ours}, open('look/ours.json', 'w'))
