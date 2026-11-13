# One-off probe (owner, 2026-11-13): facts for the new reel samples, read from their sources. claude/nla-probe only.
import json, re, urllib.request, urllib.parse, html
H = {'User-Agent': 'FBLegendsBot/1.0 (football stats reels; contact via github)'}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60) as r: return r.read().decode('utf8', 'replace')
def text(h): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()
# Pochettino's managerial table
h = get('https://en.wikipedia.org/api/rest_v1/page/html/Mauricio_Pochettino')
i = h.find('Managerial statistics'); t = h[i:i + 60000]; t = t[t.find('<table'):]; t = t[:t.find('</table>')]
for row in re.findall(r'<tr.*?</tr>', t, re.S): print('POCH', text(row))
# infobox national-team lines
for p in ['Francesco_Totti', 'Pio_Esposito', 'Harry_Kane', 'Robert_Lewandowski', 'Tijjani_Reijnders']:
    try:
        h = get('https://en.wikipedia.org/api/rest_v1/page/html/' + p); ib = h[h.find('infobox'):]; ib = ib[:ib.find('</table>')]
        for row in re.findall(r'<tr.*?</tr>', ib, re.S):
            s = text(row)
            if re.search(r'Italy|England|Poland|Netherlands|updated|correct', s): print('IB', p, s[:200])
    except Exception as e: print('IB fail', p, e)
# Manchester United's next games from our own API
for d in ['20261121','20261122','20261124','20261125','20261126','20261128','20261129','20261130','20261201','20261202','20261203','20261205','20261206','20261207']:
    try: ev = json.loads(get('https://api.football-legend.com/matches?date=' + d)).get('events', [])
    except Exception as e: print('M fail', d, e); continue
    for e in ev:
        hn, an = e['teams']['home']['name'], e['teams']['away']['name']
        if 'Manchester United' in (hn, an) or 'Man United' in (hn, an): print('MU', d, e.get('leagueSlug'), e['fixture']['date'], hn, 'v', an)
