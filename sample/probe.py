# One-off (2026-11-04): Al Ahly history video. large-v3 on the whole new reading, line by line where whisper-small
# put each line, and the club's crest (ESPN, then FotMob). Everything is written to sample/pl/ahly/ (the log is not kept).
import json, os, subprocess, urllib.request, urllib.parse
os.makedirs('sample/pl/ahly', exist_ok=True)
log = open('sample/pl/ahly/probe2.txt', 'w')
def say(*a): print(*a); log.write(' '.join(str(x) for x in a) + '\n'); log.flush()
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0; football-legend.com)'}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
for lg in ['caf.champions', 'egy.1', 'club.friendly']:
    try:
        t = json.loads(get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/teams'))
        for x in t['sports'][0]['leagues'][0]['teams']:
            tm = x['team']
            if 'ahly' in (tm.get('displayName', '') + tm.get('name', '')).lower():
                hs = [l['href'] for l in tm.get('logos', [])]
                say('espn', lg, tm['id'], tm['displayName'], hs[:2])
                if hs: open(f'sample/pl/ahly/crest-espn-{tm["id"]}.png', 'wb').write(get(hs[0]))
    except Exception as e:
        say('espn', lg, 'failed', e)
try:
    s = json.loads(get('https://www.fotmob.com/api/search/suggest?' + urllib.parse.urlencode({'term': 'Al Ahly', 'lang': 'en'})))
    say('fotmob', json.dumps(s)[:600])
except Exception as e:
    say('fotmob search failed', e)
for fid in [101918, 10032, 6408]:
    try:
        b = get(f'https://images.fotmob.com/image_resources/logo/teamlogo/{fid}.png'); open(f'sample/pl/ahly/crest-fm-{fid}.png', 'wb').write(b); say('fotmob', fid, len(b))
    except Exception as e:
        say('fotmob', fid, 'failed', e)
vm = 'sample/career/yt-ahly/voice.mp3'
if os.path.exists(vm):
    import numpy as np
    from faster_whisper import WhisperModel
    m = WhisperModel('large-v3', device='cpu', compute_type='int8')
    def pcm(a=None, b=None):
        cmd = ['ffmpeg', '-loglevel', 'error'] + (['-ss', str(a), '-to', str(b)] if a is not None else []) + ['-i', vm, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-']
        return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)
    segs, _ = m.transcribe(pcm(), language='ar')
    for s in segs: say('L', round(s.start, 2), s.text.strip())
    small = json.load(open('sample/career/yt-ahly/voice.json'))
    for s in small:
        if 'خمسة' in s['t'] or '2005' in s['t']:
            a = max(0, s['s'] - 3); seg, _ = m.transcribe(pcm(a, s['e'] + 1), language='ar'); say('2005?', a, ' '.join(x.text.strip() for x in seg))
else:
    say('no voice yet')
