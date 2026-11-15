# One-off (2026-11-15): which Nations League match of the 19:45 UK group is not yet marked finished on ESPN.
import json, urllib.request
for d in ('20261115',):
    u = f'https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.nations/scoreboard?dates={d}&limit=100'
    j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30))
    for e in j.get('events', []):
        c = e['competitions'][0]; s = e['status']['type']
        print('PROBE', e['date'], s['state'], s['detail'], '|', ' v '.join(f"{t['team']['displayName']} {t.get('score')}" for t in c['competitors']))
