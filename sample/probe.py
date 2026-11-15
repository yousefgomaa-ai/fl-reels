# One-off (2026-11-15): make tonight's Nations League full-time board again (its job was lost in a write race).
import json, os, time, urllib.parse, urllib.request
time.sleep(150)  # Cloudflare's deploy of the fix
k = urllib.parse.quote(os.environ.get('REELS_KEY', ''), safe='')
def get(q):
    u = f'https://api.football-legend.com/v2/fben/dry?key={k}&kinds=none&{q}'
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (FootballLegends probe)'}), timeout=120)).get('result', {})
print('PROBE', get('unmark=' + urllib.parse.quote('fben:slotft:uefa.nations:2026-11-15:1794772200000')).get('unmark'))
for i in range(8):
    time.sleep(45)
    st = get('state=en-ft-uefanations-20261115-1950').get('state', {})
    print('PROBE state', json.dumps(st.get('job')))
    if isinstance(st.get('job'), dict): break
