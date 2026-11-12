# One-off probe (owner, 2026-11-12): each big-five league's top scorers and assisters after the same number of rounds,
# this season and the five before, from ESPN (scoreboard + each match's key events). Prints JSON; never merged.
import json, sys, time, collections, urllib.request, concurrent.futures as cf
H = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36'}
def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r: return json.loads(r.read())
        except Exception as e:
            err = e; time.sleep(2 + 4 * i)
    raise err
LG = {'eng.1': 'Premier League', 'esp.1': 'LaLiga', 'ger.1': 'Bundesliga', 'ita.1': 'Serie A', 'fra.1': 'Ligue 1'}
def events(lg, y):
    ev = []
    import datetime as dt
    for a, b in [(f'{y}0701', f'{y}0930'), (f'{y}1001', f'{y}1130'), (f'{y}1201', f'{y + 1}0131')]:
        try: L = get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard?dates={a}-{b}', tries=2).get('events', [])
        except Exception: L = None
        if not L or len(L) < 20:  # a range refused (HTTP 400) or cut short: day by day
            L, d0, d1 = [], dt.date(int(a[:4]), int(a[4:6]), int(a[6:])), dt.date(int(b[:4]), int(b[4:6]), int(b[6:]))
            while d0 <= d1:
                if d0 <= dt.date.today():
                    try: L += get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard?dates={d0:%Y%m%d}').get('events', [])
                    except Exception as e: print('day fail', lg, d0, e, file=sys.stderr)
                d0 += dt.timedelta(days=1)
        for e in L:
            c = e['competitions'][0]
            if not c['status']['type'].get('completed'): continue
            t = {x['homeAway']: x['team'] for x in c['competitors']}
            ev.append({'id': e['id'], 'date': e['date'], 'h': t['home']['id'], 'a': t['away']['id'], 'hn': t['home']['displayName'], 'an': t['away']['displayName']})
    return sorted({e['id']: e for e in ev}.values(), key=lambda e: e['date'])
SAMPLE = []
def keyev(lg, eid):
    d = get(f'https://site.web.api.espn.com/apis/site/v2/sports/soccer/{lg}/summary?event={eid}')
    out = []
    for k in d.get('keyEvents', []) or []:
        if not k.get('scoringPlay'): continue
        txt = (k.get('type') or {}).get('text', '')
        ps = [p.get('athlete', {}).get('displayName') for p in k.get('participants', []) or []]
        tid = (k.get('team') or {}).get('id')
        if not SAMPLE: SAMPLE.append({'type': txt, 'ps': ps, 'text': k.get('text', '')[:160]})
        out.append({'type': txt, 'own': 'own' in txt.lower(), 'ps': ps, 'team': tid, 'text': k.get('text', '')})
    return out
def run(lg):
    cur = events(lg, 2026)
    order = collections.defaultdict(list)
    for e in cur: order[e['h']].append(e['id']); order[e['a']].append(e['id'])
    games = collections.Counter(len(v) for v in order.values()); N = games.most_common(1)[0][0]
    out = {'league': LG[lg], 'N': N, 'games': dict(games), 'seasons': {}}
    for y in [2026, 2025, 2024, 2023, 2022, 2021]:
        ev = cur if y == 2026 else events(lg, y)
        order = collections.defaultdict(list)
        for e in ev: order[e['h']].append(e['id']); order[e['a']].append(e['id'])
        keep = {t: set(v[:N]) for t, v in order.items()}
        ms = [e for e in ev if e['id'] in keep[e['h']] or e['id'] in keep[e['a']]]
        g, a, team, extra = collections.Counter(), collections.Counter(), {}, []
        def one(e): return e, keyev(lg, e['id'])
        with cf.ThreadPoolExecutor(6) as ex:
            for e, ks in ex.map(one, ms):
                for k in ks:
                    side = 'h' if k['team'] == e['h'] else 'a' if k['team'] == e['a'] else None
                    if side is None or e['id'] not in keep[e[side]] or k['own'] or not k['ps']: continue
                    tn = e['hn'] if side == 'h' else e['an']
                    g[k['ps'][0]] += 1; team[k['ps'][0]] = tn
                    if len(k['ps']) > 1 and k['ps'][1]: a[k['ps'][1]] += 1; team.setdefault(k['ps'][1], tn)
        top = lambda c: [{'name': n, 'team': team.get(n, ''), 'n': v} for n, v in c.most_common(8)]
        out['seasons'][y] = {'matches': len(ms), 'teams': len(order), 'last': ms[-1]['date'] if ms else '', 'goals': top(g), 'assists': top(a)}
        print(lg, y, len(ms), file=sys.stderr, flush=True)
    return out
# The two active all-time scorers (Wikipedia: Salah 193 PL as of 25 Oct 2026; Mbappé 74 UCL as of 4 Nov 2026).
def check():
    for lg, a, b, who in [('eng.1', '20261024', '20261112', 'Salah'), ('uefa.champions', '20261020', '20261112', 'Mbapp')]:
        import datetime as dt
        L, d0 = [], dt.date(int(a[:4]), int(a[4:6]), int(a[6:]))
        while d0 <= dt.date(int(b[:4]), int(b[4:6]), int(b[6:])):
            try: L += get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard?dates={d0:%Y%m%d}').get('events', [])
            except Exception: pass
            d0 += dt.timedelta(days=1)
        for e in L:
            if not any(x in e['name'] for x in ['Liverpool', 'Real Madrid']): continue
            ks = keyev(lg, e['id'])
            print('CHECK', lg, e['date'], e['name'], e['competitions'][0]['status']['type']['name'], [k['ps'] for k in ks if any(who in (p or '') for p in k['ps'])], flush=True)
try: check()
except Exception as e: print('CHECK failed', e)
with cf.ThreadPoolExecutor(5) as ex:
    for r in ex.map(run, list(LG)):
        print('RESULT ' + json.dumps(r, ensure_ascii=False), flush=True)
print('SAMPLE', SAMPLE)
