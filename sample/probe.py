# One-off (2026-11-18): (1) why the Nations League final tables reel was not made (#704's reasons); (2) the league stars
# who scored in the break: their club now and their league goals this season (FotMob), for the «back from the break» reel.
import json, os, time, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36'}
def get(u, h=H):
    try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60))
    except Exception as e: return {'error': str(e)}
names = ['Vinicius Junior', 'Erling Haaland', 'Florian Wirtz', 'Tijjani Reijnders', 'Julian Alvarez', 'Rasmus Hojlund', 'Pio Esposito', 'Christian Pulisic', 'Harry Kane', 'Mohamed Salah', 'Viktor Gyokeres', 'Achraf Hakimi', 'Jonathan David', 'Nico Paz', 'Franco Mastantuono', 'Nicolas Jackson', 'Kylian Mbappe', 'Raphinha', 'Alexander Isak', 'Lamine Yamal', 'Ousmane Dembele', 'Lautaro Martinez']
for n in names:
    s = get('https://www.fotmob.com/api/search/suggest?' + urllib.parse.urlencode({'term': n, 'lang': 'en'}))
    opts = [o for g in (s if isinstance(s, list) else []) for x in g.get('suggestions', []) for o in [x] if x.get('type') == 'player']
    if not opts: print('PROBE player', n, 'not found', str(s)[:150]); continue
    pid = opts[0]['id']
    d = get(f'https://www.fotmob.com/api/data/playerData?id={pid}')
    team = (d.get('primaryTeam') or {}).get('teamName')
    st = d.get('mainLeague') or {}
    stats = {x.get('title'): x.get('value') for x in st.get('stats', [])} if isinstance(st, dict) else {}
    print('PROBE player', n, '|', opts[0].get('name'), pid, '|', team, '|', st.get('leagueName'), st.get('season'), json.dumps(stats, ensure_ascii=False)[:200])
time.sleep(60)
x = get('https://api.football-legend.com/v2/fben/dry?' + urllib.parse.urlencode({'key': K, 'kinds': 'nlfinal'}), {'User-Agent': 'fl-probe'})
print('PROBE nlfinal', json.dumps(x.get('result', x), ensure_ascii=False)[:1500])
