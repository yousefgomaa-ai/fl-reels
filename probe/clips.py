# One-off (owner, 2026-11-17): frames of the Commons clips to pick from by eye, through the 720p copy Commons keeps.
import json, urllib.request, urllib.parse, hashlib, subprocess, re, html, os
UA = 'FootballLegendsReels/1.0 (https://football-legend.com)'
import time
F = ["20110611-wsg-swarovski-wattens-vs-fc-blau-weiß-linz-relegation-david-wimleitner-hält-den-elfmeter-von-armin-hobel.webm",
 "2022 FIFA World Cup's first goal by Enner Valencia of Ecuador against Qatar.webm", "Penalty Max-Alain Gradel (2018-04-21).ogv",
 "Còrner València-Llevant.webm", "FC Utrecht takes a Corner.ogv", "Train like a Real Madrid goalkeeper! - Courtois, Lunin & Altube.webm",
 "Germans celebrating goal against Japan in 2022 FIFA World Cup.webm", "Japanese players celebrating goals against Germany at the FIFA World Cup 2022.webm"]
out = []
os.makedirs('probe/img', exist_ok=True)
for i, f in enumerate(F):
    n = f.replace(' ', '_'); h = hashlib.md5(n.encode()).hexdigest(); e = urllib.parse.quote(n)
    md = json.load(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', 'titles': 'File:' + f, 'prop': 'imageinfo', 'iiprop': 'extmetadata|url'}), headers={'User-Agent': UA}), timeout=30))
    ii = list(md['query']['pages'].values())[0]['imageinfo'][0]; em = ii['extmetadata']
    art = re.sub('<[^>]+>', '', html.unescape(em.get('Artist', {}).get('value', ''))).strip()[:80]
    url = None
    for q in ['720p.vp9.webm', '720p.webm', '480p.vp9.webm', '480p.webm']:
        u = f'https://upload.wikimedia.org/wikipedia/commons/transcoded/{h[0]}/{h[:2]}/{e}/{e}.{q}'
        try:
            time.sleep(1); r = urllib.request.urlopen(urllib.request.Request(u, method='HEAD', headers={'User-Agent': UA}), timeout=20)
            if r.status == 200: url = u; break
        except Exception: pass
    url = url or ii['url']
    time.sleep(4)
    loc = f'probe/v{i}.bin'
    subprocess.run(['curl', '-sSL', '--retry', '4', '--retry-delay', '8', '-A', UA, '-o', loc, url])
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', loc], capture_output=True, text=True).stdout.strip() or 0)
    step = 1 if dur <= 25 else max(1, int(dur // 24))
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', loc, '-vf', f'fps=1/{step},scale=240:-2,tile=6x4', '-frames:v', '1', '-y', f'probe/img/c{i}.jpg'], capture_output=True, text=True)
    print(i, url[-60:], dur, step, r.stderr[-200:])
    os.remove(loc)
    out.append({'i': i, 'file': f, 'artist': art, 'license': em.get('LicenseShortName', {}).get('value', ''), 'url': url, 'dur': dur, 'step': step})
json.dump(out, open('probe/clips.json', 'w'), ensure_ascii=False, indent=1)
