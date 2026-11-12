import urllib.request
H = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'Referer': 'https://understat.com/league/EPL/2026'}
for u in ['https://understat.com/getLeagueData/EPL/2026', 'https://understat.com/getLeagueData/EPL/2025', 'https://understat.com/league/EPL/2026', 'https://understat.com/main/getLeagueData/EPL/2026', 'https://understat.com/getMatchData/26602',
          'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates=20221105', 'https://site.web.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event=633850']:
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40) as r:
            b = r.read().decode('utf-8', 'replace'); print('==', u, r.status, len(b)); print(b[:500].replace('\n', ' '))
            i = b.find('JSON.parse'); print('JSONparse at', i, b[i-60:i+80] if i >= 0 else '')
    except Exception as e: print('==', u, 'ERR', e)
