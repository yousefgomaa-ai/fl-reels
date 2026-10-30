# The automatic long YouTube videos (owner, 2026-10-30): «ملخص الجولة» and «قبل القمة», built from the site's data only.
# Every line of the narration comes from a template in MSA filled with the job's data (no AI writing, so no invented
# facts), one scene per line, and each line keeps the numbers it says (nums) for the whisper check.
import json, re
from arnum import count, number, ordinal, clock, GOAL, POINT, MATCH, PLAYER, TIME

LATIN = re.compile('[A-Za-z]')
esc = lambda s: str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


class Script:
    def __init__(self):
        self.lines = []

    def add(self, text, nums, scene, chap=None):
        self.lines.append({'text': text, 'nums': list(nums), 'scene': scene, 'chap': chap})


def ar(s):
    # Names the narrator can read: Arabic letters only (a Latin name is shown on screen but never read).
    return bool(s) and not LATIN.search(s)


def score_words(a, b):
    """«بثلاثة أهداف مقابل هدف», «بهدفين نظيفين», «بهدف لكل فريق»: the winner's goals first. Returns (text, numbers)."""
    g = lambda n: 'هدف' if n == 1 else count(n, GOAL)
    if a == b:
        return ('دون أهداف', []) if a == 0 else (f'ب{g(a)} لكل فريق', [a])
    if b == 0:
        return {1: ('بهدف نظيف', [1]), 2: ('بهدفين نظيفين', [2])}.get(a) or (f'ب{count(a, GOAL)} نظيفة', [a])
    return f'ب{g(a)} مقابل {g(b)}', [a, b]


def li(name):
    # «لأستون فيلا», «للأهلي»: the preposition joined to the name.
    return 'لل' + name[2:] if name.startswith('ال') else 'ل' + name


def join_and(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else '، و'.join(xs[:-1]) + '، و' + xs[-1] if len(xs) > 2 else ' و'.join(xs)


def scorer_words(goals, side):
    """«محمد صلاح مرتين، وهوغو إيكيتيكي»: a side's scorers in order; None when a name cannot be read."""
    seen = {}
    for x in goals:
        if x['side'] != side or x.get('og'):
            continue
        seen[x['player']] = seen.get(x['player'], 0) + 1
    og = sum(1 for x in goals if x['side'] == side and x.get('og'))
    if any(not ar(p) for p in seen):
        return None, []
    parts, nums = [], []
    for p, n in seen.items():
        parts.append(p if n == 1 else f'{p} {count(n, TIME)}' if n > 2 else f'{p} مرتين')
        if n > 1: nums.append(n)
    if og:
        parts.append('هدف عكسي' if og == 1 else f'{count(og, GOAL)} عكسية')
        if og > 1: nums.append(og)
    return (join_and(parts) if parts else ''), nums


def page(css, body, chip, extra_head=''):
    return f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><link rel="stylesheet" href="../fonts/fonts.css"><style>{css}</style>{extra_head}</head>
<body>{body}<div id="cap"></div><div id="progw"><div id="prog"></div></div><script src="../engine.js"></script>
<script>
// A long name is made smaller until it fits its box: nothing may be wider than the frame (owner, 2026-10-30).
function fitAll(){{document.querySelectorAll('.fit').forEach((el)=>{{let s=parseFloat(getComputedStyle(el).fontSize);while(el.scrollWidth>el.clientWidth+1&&s>16){{s-=2;el.style.fontSize=s+'px';}}}});}}
document.fonts.ready.then(fitAll);
</script></body></html>'''


# ---------------------------------------------------------------- «ملخص الجولة»
def round_video(job, L):
    lg, n, T = job['league'], job.get('round'), job['table']
    ms = job['matches']
    rank = {r['team']: r['rank'] for r in T}
    S = Script()
    def res(m, kick):
        gl = ''.join(f'<div class="g fit" data-in><b>{esc(g["min"])}\'</b> {esc(g["player"] if not g.get("og") else "هدف عكسي")}</div>' for g in sorted(m.get('goals') or [], key=lambda g: mins(g['min'])))[:6000]
        return f'''<div class="kick fit" data-in="0.1">{esc(kick)}</div><div class="res" data-in="0.2">
<div class="tm"><img src="{L(m['homeLogo'])}"><span class="fit">{esc(m['home'])}</span></div><div class="sc"><b data-n="{m['hs']}" data-d="0.6">{m['hs']}</b><i>-</i><b data-n="{m['as']}" data-d="0.9">{m['as']}</b></div>
<div class="tm"><img src="{L(m['awayLogo'])}"><span class="fit">{esc(m['away'])}</span></div></div><div class="gs">{gl}</div>'''
    def tile(v, label, cls=''):
        return f'<div class="tile {cls}" data-in><b data-n="{v}" data-d="0.4">{v}</b><span class="fit">{esc(label)}</span></div>'
    def trow(r, hi=''):
        gd = r['gf'] - r['ga']
        return f'''<div class="tr {hi}" data-in data-dir="X" data-dist="-60"><b>{r["rank"]}</b><img src="{L(r["logo"])}"><span class="fit">{esc(r["team"])}</span><em>{r["played"]}</em><em><bdi dir="ltr">{"+" if gd > 0 else ""}{gd}</bdi></em><strong data-n="{r["pts"]}">{r["pts"]}</strong></div>'''
    rd = f' {ordinal(n, True)}' if n else ''
    S.add(f'أهلًا بكم في ملخص الجولة{rd} من {lg}: النتائج، والهدافون، والترتيب بعد الجولة.', [n] if n else [],
          f'<div class="hero"><div class="tag" data-in>{esc(lg)}</div><div class="big" data-in>الجولة <b>{n or ""}</b></div><div class="sub" data-in>ملخص الجولة</div></div>', 'المقدمة')
    goals = sum(m['hs'] + m['as'] for m in ms)
    hw = sum(m['hs'] > m['as'] for m in ms); aw = sum(m['hs'] < m['as'] for m in ms); dr = len(ms) - hw - aw
    t = f'شهدت الجولة {count(len(ms), MATCH)}، {"وسُجّل فيها " + count(goals, GOAL) if goals else "ولم يُسجَّل فيها أي هدف"}. '
    nums = [len(ms), goals]
    parts = []
    if hw: parts.append(f'فاز أصحاب الأرض في {count(hw, MATCH)}'); nums.append(hw)
    if aw: parts.append(f'والضيوف في {count(aw, MATCH)}' if hw else f'فاز الضيوف في {count(aw, MATCH)}'); nums.append(aw)
    if dr: parts.append(f'وانتهت {count(dr, MATCH, nom=True)} بالتعادل' if dr > 1 else 'وانتهت مباراة واحدة بالتعادل'); nums.append(dr)
    t += '، '.join(parts) + '.'
    S.add(t, nums, '<div class="kick" data-in>الجولة في سطر</div><div class="tiles">' + tile(len(ms), 'مباريات') + tile(goals, 'أهداف') + tile(hw, 'فوز لأصحاب الأرض') + tile(aw, 'فوز للضيوف') + tile(dr, 'تعادلات') + '</div>')
    # The results: the matches of the table's top sides first; goalless draws together at the end.
    leader = T[0]['team'] if T else None
    big = max(ms, key=lambda m: (abs(m['hs'] - m['as']), m['hs'] + m['as']))
    most = max(ms, key=lambda m: (m['hs'] + m['as'], abs(m['hs'] - m['as'])))
    order = sorted([m for m in ms if m['hs'] + m['as']], key=lambda m: min(rank.get(m['home'], 99), rank.get(m['away'], 99)))
    zero = [m for m in ms if not m['hs'] + m['as']]
    win_t = ['{W} فاز على {L} {S}{where}.', 'وحقق {W} الفوز على {L} {S}{where}.', 'وخسر {L} أمام {W} {S}{where2}.', 'وتغلّب {W} على {L} {S}{where}.']
    draw_t = ['وتعادل {H} مع {A} {S}.', 'وانتهت مباراة {H} و{A} بالتعادل {S}.']
    first = True
    for i, m in enumerate(order):
        kick = 'مباراة المتصدر' if leader in (m['home'], m['away']) else 'أثقل نتيجة في الجولة' if m is big and abs(m['hs'] - m['as']) >= 3 else 'أكثر مباراة أهدافًا' if m is most and m['hs'] + m['as'] >= 5 else 'نتائج الجولة'
        if m['hs'] != m['as']:
            hwin = m['hs'] > m['as']
            W, Lo = (m['home'], m['away']) if hwin else (m['away'], m['home'])
            st, sn = score_words(max(m['hs'], m['as']), min(m['hs'], m['as']))
            text = win_t[i % len(win_t)].format(W=W, L=Lo, S=st, where=' على أرضه' if hwin else ' خارج أرضه', where2=' على أرضه' if not hwin else ' خارج أرضه')
            sides = ['home', 'away'] if hwin else ['away', 'home']
            names = {'home': m['home'], 'away': m['away']}
        else:
            st, sn = score_words(m['hs'], m['as'])
            text = draw_t[i % len(draw_t)].format(H=m['home'], A=m['away'], S=st)
            sides, names = ['home', 'away'], {'home': m['home'], 'away': m['away']}
        nums = list(sn)
        gl = m.get('goals')
        if gl and len(gl) == m['hs'] + m['as']:
            said = []
            for sd in sides:
                w, wn = scorer_words(gl, sd)
                if w is None: said = None; break
                if w: said.append(f'{li(names[sd])}: {w}'); nums += wn
            if said: text += ' سجّل ' + '، وسجّل '.join(said) + '.'
        if not ar(text):
            return None, f'a name in Latin letters: {m["home"]} / {m["away"]}'
        S.add(('ونبدأ بالنتائج: ' if first else '') + text, nums, res(m, kick), 'النتائج' if first else None)
        first = False
    if zero:
        mini = '<div class="kick" data-in>دون أهداف</div><div class="mini">' + ''.join(f'<div class="mr" data-in><img src="{L(m["homeLogo"])}"><span class="fit">{esc(m["home"])}</span><b><i>0</i> - <i>0</i></b><span class="fit">{esc(m["away"])}</span><img src="{L(m["awayLogo"])}"></div>' for m in zero[:5]) + '</div>'
        pairs = join_and([f'{m["home"]} و{m["away"]}' if len(zero) > 1 else f'{m["home"]} مع {m["away"]}' for m in zero])
        text = f'وتعادل {pairs} دون أهداف.' if len(zero) == 1 else f'وانتهت {count(len(zero), MATCH, nom=True)} دون أهداف: {pairs}.'
        S.add(text, [len(zero)] if len(zero) > 1 else [], mini, 'النتائج' if first else None)
    # The round's scorer: two goals or more.
    tally = {}
    for m in ms:
        for g in m.get('goals') or []:
            if not g.get('og'):
                k = (g['player'], m['home'] if g['side'] == 'home' else m['away'])
                tally[k] = tally.get(k, 0) + 1
    if tally:
        (pl, team), gn = max(tally.items(), key=lambda kv: kv[1])
        if gn >= 2 and ar(pl) and sum(v == gn for v in tally.values()) == 1:
            S.add(f'وهداف الجولة {pl}، لاعب {team}، بتسجيله {count(gn, GOAL)}.', [gn],
                  f'<div class="kick" data-in>هداف الجولة</div><div class="duo"><div class="stat" data-in><b data-n="{gn}">{gn}</b><span class="fit">{esc(pl)} • {esc(team)}</span></div></div>')
    # The table: the top places, then the bottom three.
    top = T[:max(3, min(job.get('top') or 4, 4))]
    if len(T) >= 8:
        a, b = T[0], T[1]
        t = f'وإلى الترتيب: {a["team"]} في الصدارة برصيد {count(a["pts"], POINT)}'
        nums = [a['pts']]
        if a['pts'] == b['pts']:
            t += f'، ويتساوى معه {b["team"]} في النقاط لكنه يتأخر بفارق الأهداف'
        else:
            t += f'، بفارق {count(a["pts"] - b["pts"], POINT)} عن {b["team"]} صاحب المركز الثاني'; nums += [a['pts'] - b['pts'], 2]
        adv = ['', '', 'ثانيًا', 'ثالثًا', 'رابعًا', 'خامسًا']
        rest = [f'{r["team"]} {adv[r["rank"]]} برصيد {count(r["pts"], POINT)}' for r in top[2:]]
        nums += [x for r in top[2:] for x in (r['rank'], r['pts'])]
        if a['pts'] != b['pts']: nums.append(b['pts']); t += f' برصيد {count(b["pts"], POINT)}'
        t += ('. و' + '، و'.join(rest) if rest else '') + '.'
        if not ar(t): return None, 'a team name in Latin letters in the table'
        head = '<div class="th" data-in><b>#</b><span></span><span>الفريق</span><em>لعب</em><em>الفارق</em><strong>نقاط</strong></div>'
        S.add(t, nums, f'<div class="kick" data-in>الترتيب بعد الجولة {n or ""} • الصدارة</div><div class="table">{head}' + ''.join(trow(r, 'top') for r in top) + '</div>', 'الترتيب')
        low = T[-3:]
        z, y, x = low[2], low[1], low[0]
        t = f'وفي القاع، {z["team"]} في المركز الأخير برصيد {count(z["pts"], POINT)}، وقبله {y["team"]} برصيد {count(y["pts"], POINT)}، ثم {x["team"]} برصيد {count(x["pts"], POINT)}.'
        if not ar(t): return None, 'a team name in Latin letters in the table'
        S.add(t, [z['pts'], y['pts'], x['pts']], '<div class="kick" data-in>القاع</div><div class="table">' + ''.join(trow(r, 'low') for r in low) + '</div>')
        att = max(T, key=lambda r: r['gf']); dfn = min(T, key=lambda r: r['ga'])
        if sum(r['gf'] == att['gf'] for r in T) == 1 and sum(r['ga'] == dfn['ga'] for r in T) == 1:
            dt = f'لم تهتز شباكه في {count(dfn["played"], MATCH)}' if not dfn['ga'] else f'إذ استقبل {count(dfn["ga"], GOAL)} فقط في {count(dfn["played"], MATCH)}'
            S.add(f'وبالأرقام: {att["team"]} صاحب أقوى هجوم بـ{count(att["gf"], GOAL)}، و{dfn["team"]} صاحب أقوى دفاع، {dt}.', [att['gf'], dfn['ga'], dfn['played']] if dfn['ga'] else [att['gf'], dfn['played']],
                  f'<div class="kick" data-in>أرقام الموسم حتى الآن</div><div class="duo"><div class="stat" data-in><img src="{L(att["logo"])}"><b data-n="{att["gf"]}">{att["gf"]}</b><span class="fit">أقوى هجوم: {esc(att["team"])}</span></div><div class="stat" data-in><img src="{L(dfn["logo"])}"><b data-n="{dfn["ga"]}">{dfn["ga"]}</b><span class="fit">أقوى دفاع: {esc(dfn["team"])}</span></div></div>', 'أرقام الموسم')
    nx = [m for m in job.get('next') or [] if ar(m['home'] + m['away'])][:3]
    if nx:
        nn = job.get('nextRound')
        t = f'وفي الجولة {ordinal(nn, True) + " " if nn else ""}المقبلة: ' + '، و'.join(f'{m["home"]} يستضيف {m["away"]}' for m in nx) + '.'
        S.add(t, [nn] if nn else [], f'<div class="kick" data-in>الجولة {nn or "المقبلة"}</div><div class="mini">' + ''.join(f'<div class="mr" data-in><img src="{L(m["homeLogo"])}"><span class="fit">{esc(m["home"])}</span><b>×</b><span class="fit">{esc(m["away"])}</span><img src="{L(m["awayLogo"])}"></div>' for m in nx) + '</div>', 'الجولة المقبلة')
    S.add(f'من كان نجم الجولة{rd} في رأيكم؟ اكتبوه في التعليقات، وتابعوا القناة ليصلكم ملخص كل جولة.', [n] if n else [],
          '<div class="hero"><div class="big" data-in style="font-size:120px">نجم الجولة؟</div><div class="sub" data-in>اكتبه في التعليقات 👇</div><div class="tag" data-in>تابع القناة: ملخص كل جولة</div></div>')
    css = open(__file__.replace('build.py', 'round.css')).read()
    body = '<div class="bg"></div><div class="grid"></div><div class="brand">FOOTBALL <i>LEGENDS</i></div><div class="chip">ملخص الجولة</div>' + ''.join(f'<div class="scene" style="opacity:0">{l["scene"]}</div>' for l in S.lines)
    title = f'ملخص الجولة {n or ""} من {lg}: النتائج والأهداف والترتيب'.replace('  ', ' ')
    best = max(ms, key=lambda m: m['hs'] + m['as'])
    summary = '\n'.join(f'⚽ {m["home"]} {m["hs"]} - {m["as"]} {m["away"]}' for m in ms)
    meta = {'title': title, 'about': f'كل نتائج الجولة {n or ""} من {lg} وهدافوها، والترتيب بعد الجولة، وأرقام الموسم.\n\n{summary}',
            'tags': [lg, f'ترتيب {lg}', f'نتائج {lg}', 'ملخص الجولة', best['home'], best['away']]}
    return (S, page(css, body, 'ملخص الجولة'), meta), None


def mins(m):
    a = re.findall(r'\d+', str(m))
    return int(a[0]) + (int(a[1]) / 100 if len(a) > 1 else 0) if a else 999


# ---------------------------------------------------------------- «قبل القمة»
DAYS = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']


def duel(label, x, y, m):
    return f'<div class="du" data-in><div class="v l">{x}</div><div class="bars"><div class="bl"><i data-w="{100 * x / m:.1f}"></i></div><span>{label}</span><div class="ba"><i data-w="{100 * y / m:.1f}"></i></div></div><div class="v a">{y}</div></div>'


def preview_video(job, L, colors):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    lg, n, H, A = job['league'], job.get('round'), job['home'], job['away']
    h, a = H['name'], A['name']
    if not ar(h + a): return None, f'a team name in Latin letters: {h} / {a}'
    k = datetime.fromtimestamp(job['ko'] / 1000, ZoneInfo('Africa/Cairo'))
    S = Script()
    hl, al = L(H['logo']), L(A['logo'])
    rd = f'الجولة {ordinal(n, True)} من ' if n else ''
    S.add(f'أهلًا بكم في «قبل القمة». قمة {rd}{lg} تجمع {h} و{a}، وهذا كل ما تحتاج معرفته قبل المباراة.', [n] if n else [],
          f'<div class="kick fit" data-in>قمة الجولة {n or ""} • {esc(lg)}</div><div class="vs" data-in><img src="{hl}"><b>×</b><img src="{al}"></div><div class="ttl fit" data-in>{esc(h)} × {esc(a)}</div><div class="pill" data-in>كل ما تحتاج معرفته</div>', 'المقدمة')
    ck, hh = clock(k.hour, k.minute)
    day = DAYS[k.weekday()]
    venue, tv = job.get('venue') or '', job.get('tv') or ''
    t = f'تُقام المباراة يوم {day} المقبل، {ck} بتوقيت القاهرة' + (f'، على ملعب {venue}' if ar(venue) else '') + (f'، وتنقلها {tv}' if ar(tv) else '') + '.'
    boxes = f'<div><span>اليوم</span><b class="fit">{day}</b></div><div><span>الموعد</span><b>{k.hour % 12 or 12}:{k.minute:02d} {"م" if k.hour >= 12 else "ص"}</b><i>بتوقيت القاهرة</i></div>'
    if venue: boxes += f'<div><span>الملعب</span><b class="fit">{esc(venue)}</b></div>'
    elif tv: boxes += f'<div><span>القناة</span><b class="fit">{esc(tv)}</b></div>'
    S.add(t, [hh], f'<div class="info" data-in>{boxes}</div>', 'الموعد')
    hr, arw = H.get('row'), A.get('row')
    def side(T, row, cls, logo):
        rows = [('المركز', row['rank']), ('النقاط', row['pts']), ('فوز • تعادل • هزيمة', f'{row["w"]} • {row["d"]} • {row["l"]}')]
        return f'<div class="card {cls}" data-in><img src="{logo}"><h2 class="fit">{esc(T)}</h2>' + ''.join(f'<div class="r"><span>{x}</span><b>{v}</b></div>' for x, v in rows) + '</div>'
    def side_line(T, row, lead):
        w, d, l = row['w'], row['d'], row['l']
        rec = join_and([x for x in [count(w, ('فوز واحد', 'فوزين', 'فوزان', 'انتصارات', 'فوزًا', False)) if w else '', count(d, ('تعادل واحد', 'تعادلين', 'تعادلان', 'تعادلات', 'تعادلًا', False)) if d else '', count(l, ('هزيمة واحدة', 'هزيمتين', 'هزيمتان', 'هزائم', 'هزيمة', True)) if l else ''] if x])
        return f'{lead}{T} المركز {ordinal(row["rank"])} برصيد {count(row["pts"], POINT)}، بعد {rec}.', [row['rank'], row['pts']] + [x for x in (w, d, l) if x]
    if hr and arw:
        for T, row, cls, logo, lead in ((h, hr, 'h', hl, 'يحتل '), (a, arw, 'a', al, 'بينما يحتل ضيفه ')):
            t, nums = side_line(T, row, lead)
            note = ''
            if row['rank'] == 1: note = '<div class="note" data-in>المتصدر</div>'
            S.add(t, nums, side(T, row, cls, logo) + note, 'الترتيب' if cls == 'h' else None)
        mx = max(hr['gf'], arw['gf'], hr['ga'], arw['ga'], 1)
        pm = max(hr['pts'], arw['pts'], 1)
        t = f'هجوميًا، سجّل {h} {count(hr["gf"], GOAL)} واستقبل {count(hr["ga"], GOAL)}، مقابل {count(arw["gf"], GOAL)} سجّلها {a} و{count(arw["ga"], GOAL)} استقبلها.'
        S.add(t, [hr['gf'], hr['ga'], arw['gf'], arw['ga']], '<div class="kick" data-in>وجهًا لوجه هذا الموسم</div><div class="duels">' + duel('سجّل', hr['gf'], arw['gf'], mx) + duel('استقبل', hr['ga'], arw['ga'], mx) + duel('النقاط', hr['pts'], arw['pts'], pm) + '</div>')
    fm = job.get('form') or {}
    if len(fm.get('home') or '') >= 3 and len(fm.get('away') or '') >= 3:
        fh, fa = fm['home'][-5:], fm['away'][-5:]
        chips = lambda f: ''.join(f'<em class="{ {"W": "w", "D": "d", "L": "l"}[c] }">{ {"W": "ف", "D": "ت", "L": "خ"}[c] }</em>' for c in f)
        wh, wa = fh.count('W'), fa.count('W')
        say = lambda T, f, w: f'فاز {T} في {count(w, MATCH)}' if w else f'لم يفز {T} في أي منها'
        same = len(fh) == len(fa)
        t = (f'وفي آخر {count(len(fh), MATCH)}، ' if same else 'وفي المباريات الأخيرة، ') + f'{say(h, fh, wh)}، بينما {say(a, fa, wa)}.'
        S.add(t, ([len(fh)] if same else []) + [x for x in (wh, wa) if x],
              f'<div class="kick" data-in>آخر المباريات</div><div class="sc2"><div class="o h" data-in><img src="{hl}"><span class="fit">{esc(h)}</span><div class="fl">{chips(fh)}</div></div><div class="o a" data-in><img src="{al}"><span class="fit">{esc(a)}</span><div class="fl">{chips(fa)}</div></div></div>', 'المستوى')
    hh2 = job.get('h2h') or {}
    if hh2.get('meetings'):
        m, hw, dr, aw = hh2['meetings'], hh2['homeWins'], hh2['draws'], hh2['awayWins']
        parts = [f'فاز {h} في {count(hw, MATCH)}' if hw else f'لم يفز {h} في أي منها', f'وفاز {a} في {count(aw, MATCH)}' if aw else f'ولم يفز {a} في أي منها']
        if dr: parts.append(f'وانتهت {count(dr, MATCH, nom=True)} بالتعادل' if dr > 1 else 'وانتهت مباراة واحدة بالتعادل')
        t = f'وبحسب سجل المواجهات المتاح، التقى الفريقان في {count(m, MATCH)}: ' + '، '.join(parts) + '.'
        S.add(t, [m] + [x for x in (hw, aw, dr) if x], '<div class="kick" data-in>المواجهات المباشرة</div><div class="duels">' + duel('فوز', hw, aw, max(hw, aw, 1)) + f'<div class="note" data-in style="align-self:center">{dr} تعادل • {m} مباراة</div></div>', 'المواجهات')
        last = [x for x in hh2.get('last') or [] if ar(x['host'] + x['guest'])][:2]
        if last:
            x = last[0]
            if x['hs'] == x['gs']:
                st, sn = score_words(x['hs'], x['gs'])
                t = f'وانتهت آخر مواجهة بينهما بالتعادل {st}' if x['hs'] else 'وانتهت آخر مواجهة بينهما بالتعادل دون أهداف'
            else:
                W = x['host'] if x['hs'] > x['gs'] else x['guest']
                st, sn = score_words(max(x['hs'], x['gs']), min(x['hs'], x['gs']))
                t = f'وانتهت آخر مواجهة بينهما بفوز {W} {st}'
            t += f'، على أرض {x["host"]}.' if x['host'] in (h, a) else '.'
            cards = ''.join(f'<div class="m" data-in><span>{esc(y.get("date") or "")}</span><b class="sl"><span class="fit">{esc(y["host"])}</span><span>{y["hs"]}</span><span>-</span><span>{y["gs"]}</span><span class="fit">{esc(y["guest"])}</span></b></div>' for y in last)
            S.add(t, sn, f'<div class="kick" data-in>آخر المواجهات</div><div class="h2h">{cards}</div>')
    ab = job.get('absences') or {}
    for T, lst, logo in ((h, ab.get('home') or [], hl), (a, ab.get('away') or [], al)):
        if not lst: continue
        typ = lambda x: 'إيقاف' if x == 'suspension' else 'إصابة' if x == 'injury' else 'غياب'
        names = [x['name'] for x in lst]
        t = f'ويغيب عن {T} {count(len(lst), PLAYER, nom=True)}' + (f': {join_and(names[:4])}' if all(ar(x) for x in names[:4]) else '') + ('، وغيرهم' if len(lst) > 4 and all(ar(x) for x in names[:4]) else '') + '.'
        S.add(t, [len(lst)] if len(lst) > 1 else [], f'<div class="kick" data-in>الغيابات • {esc(T)}</div><div class="news">' + ''.join(f'<div class="nw no" data-in><img src="{logo}"><span>{esc(x["name"])}</span><b>{typ(x.get("type"))}</b></div>' for x in lst[:5]) + '</div>', 'الغيابات' if T == h or not ab.get('home') else None)
    if hr and arw:
        ph, pa = hr['pts'] + 3, arw['pts'] + 3
        t = f'وماذا تعني النتيجة؟ الفوز يرفع رصيد {h} إلى {count(ph, POINT)}، وفوز {a} يرفع رصيده إلى {count(pa, POINT)}.'
        S.add(t, [ph, pa], f'<div class="kick" data-in>ماذا تعني النتيجة؟</div><div class="sc2"><div class="o h" data-in><img src="{hl}"><span class="fit">فوز {esc(h)}</span><b>{ph} نقطة</b></div><div class="o a" data-in><img src="{al}"><span class="fit">فوز {esc(a)}</span><b>{pa} نقطة</b></div></div>', 'ماذا تعني النتيجة')
    S.add('ما توقعك للنتيجة؟ اكتبه في التعليقات، وتابع القناة ليصلك «قبل القمة» قبل كل مباراة كبيرة.', [],
          f'<div class="vs" data-in><img src="{hl}"><b>?</b><img src="{al}"></div><div class="ttl" data-in>ما توقعك للنتيجة؟</div><div class="pill" data-in>اكتبه في التعليقات 👇 وتابع القناة</div>')
    hc, ac = colors
    css = open(__file__.replace('build.py', 'preview.css')).read() + f':root{{--h:{hc[0]};--hd:{hc[1]};--hl:{hc[2]};--a:{ac[0]}}}'
    body = '<div class="halfL"></div><div class="halfR"></div><div class="seam"></div><div class="brand">FOOTBALL LEGENDS</div><div class="chip">قبل القمة</div>' + ''.join(f'<div class="scene" style="opacity:0">{l["scene"]}</div>' for l in S.lines)
    meta = {'title': f'{h} × {a} | قبل القمة: كل ما تحتاج معرفته قبل مباراة {rd}{lg}'.replace('  ', ' '),
            'about': f'كل ما تحتاج معرفته قبل مباراة {h} و{a} في {lg}: الموعد يوم {day} {k.hour % 12 or 12}:{k.minute:02d} {"م" if k.hour >= 12 else "ص"} بتوقيت القاهرة، والترتيب، والمستوى، والمواجهات المباشرة، والغيابات.',
            'tags': [h, a, f'{h} و{a}', f'موعد مباراة {h} و{a}', lg, 'قبل القمة']}
    return (S, page(css, body, 'قبل القمة'), meta), None
