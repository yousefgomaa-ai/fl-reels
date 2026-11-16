# One-off (2026-11-16): is the new relay live? Today's matches whose line-ups are out and that are not finished (the
# server keeps no copy of those): through the API's FotMob path, their starters should carry fx/fy.
import json, urllib.request, datetime
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36'}
day = datetime.datetime.utcnow().strftime('%Y%m%d')
d = json.load(urllib.request.urlopen(urllib.request.Request(f'https://www.fotmob.com/api/data/matches?date={day}', headers=H), timeout=30))
cand = []
for lg in d.get('leagues', []):
    for m in lg.get('matches', []):
        st = m.get('status', {})
        if st.get('finished') or st.get('cancelled'): continue
        t = st.get('utcTime') or ''
        try: k = datetime.datetime.fromisoformat(t.replace('Z', '+00:00'))
        except Exception: continue
        mins = (k - datetime.datetime.now(datetime.timezone.utc)).total_seconds() / 60
        if mins < 55: cand.append((m['id'], lg.get('name'), m['home']['name'], m['away']['name'], round(mins)))
print('PROBE now', datetime.datetime.utcnow().strftime('%H:%M'), 'candidates', len(cand))
n = 0
for mid, lg, h, a, mins in cand:
    try:
        j = json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.football-legend.com/match/live-feed?league=fra.coupe_de_france&eventId=fm-{mid}', headers=H), timeout=60))
    except Exception as e:
        print('PROBE', mid, lg, h, a, 'error', e); continue
    for l in j.get('lineups', []):
        stt = [p for p in l.get('players', []) if p.get('starter')]
        if len(stt) < 11: continue
        print('PROBE', mid, lg, '|', h, 'v', a, f'({mins} min)', l.get('side'), l.get('formation'), 'with spots', sum(1 for p in stt if p.get('fx') is not None), '/', len(stt), stt[1])
        n += 1
    if n >= 4: break
