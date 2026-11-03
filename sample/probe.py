# One-off (2026-11-03): waits for the latest API (/v2/ytv/status) and prints why each league's round summary was or was not made.
import json, os, time, urllib.parse, urllib.request
k = urllib.parse.quote(os.environ['REELS_KEY'], safe='')
d = None
for t in range(30):
    try: d = json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.football-legend.com/v2/ytv/status?key={k}', headers={'User-Agent': 'fl-probe'}), timeout=120)); break
    except Exception as e: print('try', t, time.strftime('%H:%M:%S'), e); time.sleep(30)
if not d: raise SystemExit('the latest API is not live after 15 minutes')
print('NOW', d['now'], 'SCOPE', d['scope'])
for j in d['jobs']: print('JOB', j['id'], j['status'], j.get('note'))
for slug, x in d['leagues'].items():
    print('==', slug, 'roundDone', x['roundDone'], 'mark', x['mark'], 'last', x['last'], 'teams', x['teams'], 'roundNo', x['roundNo'], 'tableBad', x['tableBad'])
    print('   played', x['played'])
    for m in x['done'][-12:]: print('   DONE', m['d'], m['det'], m['h'], m['g'], m['a'])
    for m in x['pending'][:8]: print('   PEND', m['d'], m['st'], m['det'], m['h'], '-', m['a'])
