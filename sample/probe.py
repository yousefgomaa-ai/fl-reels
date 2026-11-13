# One-off probe (owner, 2026-11-13): facts for the new reel samples, read from their sources. claude/nla-probe only.
import json, re, urllib.request, html
H = {'User-Agent': 'FBLegendsBot/1.0 (football stats reels; contact via github)'}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60) as r: return r.read().decode('utf8', 'replace')
def text(h): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()
try:
    h = get('https://en.wikipedia.org/api/rest_v1/page/html/Mauricio_Pochettino')
    i = h.find('id="Managerial_statistics"'); t = h[i:]; t = t[t.find('<table'):]; t = t[:t.find('</table>')]
    for row in re.findall(r'<tr.*?</tr>', t, re.S): print('POCH', text(row))
    for m in re.finditer(r'Manchester United[^.]{0,200}\.', text(h)): print('POCHMU', m.group(0)[:240])
except Exception as e: print('POCH fail', e)
for p in ['Francesco_Totti', 'Pio_Esposito', 'Harry_Kane', 'Robert_Lewandowski']:
    try:
        h = get('https://en.wikipedia.org/api/rest_v1/page/html/' + p); ib = h[h.find('infobox'):]; ib = ib[:ib.find('</table>')]
        for row in re.findall(r'<tr.*?</tr>', ib, re.S):
            s = text(row)
            if re.search(r'Italy|England|Poland|as of|correct', s, re.I): print('IB', p, s[:220])
    except Exception as e: print('IB fail', p, e)
for d in ['20261121','20261122','20261124','20261125','20261126','20261128','20261129','20261130','20261201','20261202','20261203','20261205','20261206','20261207']:
    try: ev = json.loads(get('https://api.football-legend.com/matches?date=' + d)).get('events', [])
    except Exception as e: print('M fail', d, e); continue
    for e in ev:
        hn, an = e['teams']['home']['name'], e['teams']['away']['name']
        if 'Manchester United' in (hn, an) or 'Man United' in (hn, an): print('MU', d, e.get('leagueSlug'), e['fixture']['date'], hn, 'v', an, e['teams']['home'].get('logo',''), e['teams']['away'].get('logo',''))
