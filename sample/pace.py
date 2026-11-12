# One-off probe (owner, 2026-11-12): each big-five league's top scorers and assisters after the same number of rounds,
# this season and the five before, from Understat's match rosters. Prints JSON; never merged.
import json, re, sys, time, collections, urllib.request, concurrent.futures as cf
H = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest'}
def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=40) as r: return r.read().decode('utf-8', 'replace')
        except Exception as e:
            err = e; time.sleep(2 + 3 * i)
    raise err
def unq(s): return json.loads(s.encode('utf-8').decode('unicode_escape'))
def league(lg, season):
    try:
        d = json.loads(get(f'https://understat.com/getLeagueData/{lg}/{season}'))
        return d['dates']
    except Exception:
        h = get(f'https://understat.com/league/{lg}/{season}')
        return unq(re.search(r"datesData\s*=\s*JSON\.parse\('(.*?)'\)", h).group(1))
def rosters(mid):
    try:
        return json.loads(get(f'https://understat.com/getMatchData/{mid}'))['rosters']
    except Exception:
        h = get(f'https://understat.com/match/{mid}')
        return unq(re.search(r"rostersData\s*=\s*JSON\.parse\('(.*?)'\)", h).group(1))
def firstN(dates):
    done = sorted([m for m in dates if m.get('isResult')], key=lambda m: m['datetime'])
    order = collections.defaultdict(list)
    for m in done:
        order[m['h']['id']].append(m['id']); order[m['a']['id']].append(m['id'])
    return done, order
def run(lg):
    out = {'league': lg, 'seasons': {}}
    cur = league(lg, 2026)
    done, order = firstN(cur)
    games = collections.Counter(len(v) for v in order.values())
    N = games.most_common(1)[0][0]
    out['N'] = N; out['games'] = dict(games)
    for season in [2026, 2025, 2024, 2023, 2022, 2021]:
        dates = cur if season == 2026 else league(lg, season)
        done, order = firstN(dates)
        keep = {t: set(v[:N]) for t, v in order.items()}
        ms = [m for m in done if m['id'] in keep[m['h']['id']] or m['id'] in keep[m['a']['id']]]
        g, a, team, apps = collections.Counter(), collections.Counter(), {}, collections.Counter()
        for m in ms:
            r = rosters(m['id']); time.sleep(.15)
            for side in ('h', 'a'):
                tid = m[side]['id']
                if m['id'] not in keep[tid]: continue
                for p in r[side].values():
                    k = p['player']; team[k] = m[side]['title']
                    g[k] += int(p['goals']); a[k] += int(p['assists']); apps[k] += 1
        top = lambda c: [{'name': k, 'team': team[k], 'n': v, 'games': apps[k]} for k, v in c.most_common(6)]
        out['seasons'][season] = {'matches': len(ms), 'cut': max([m['datetime'] for m in ms] or ['']), 'goals': top(g), 'assists': top(a)}
        print(lg, season, len(ms), file=sys.stderr, flush=True)
    return out
with cf.ThreadPoolExecutor(5) as ex:
    for r in ex.map(lambda l: (lambda: run(l))() if True else None, ['EPL', 'La_liga', 'Bundesliga', 'Serie_A', 'Ligue_1']):
        print('RESULT ' + json.dumps(r, ensure_ascii=False), flush=True)
