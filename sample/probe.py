# One-off (2026-10-29): Nahdat Berkane v Maghreb Fes, checked again after #434 (should be one copy).
import json, urllib.request
for d in ('20261029', '20261028', '20261030'):
    j = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://api.football-legend.com/matches?date={d}', headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read())
    for m in j.get('events') or []:
        n = json.dumps(m.get('teams'), ensure_ascii=False)
        if 'erkane' in n or 'Fes' in n or 'Fès' in n or 'بركان' in n:
            print(d, m.get('id'), m.get('leagueSlug'), m.get('fixture', {}).get('date'), m.get('fixture', {}).get('status', {}).get('state'), m['teams']['home'].get('name'), '|', m['teams']['away'].get('name'), m.get('source'), json.dumps(m.get('league'), ensure_ascii=False)[:120])
