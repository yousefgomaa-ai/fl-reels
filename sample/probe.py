# One-off (2026-11-04): Al Ahly history video. large-v3 on the doubtful spots of the voice, and the club's crest from ESPN.
import json, os, subprocess, urllib.request
import numpy as np
from faster_whisper import WhisperModel
os.makedirs('sample/pl/ahly', exist_ok=True)
vm = 'sample/career/yt-ahly/voice.mp3'
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
def pcm(a, b): return np.frombuffer(subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(a), '-to', str(b), '-i', vm, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout, np.float32)
out = {}
for name, a, b in [('2005', 36.8, 44.2), ('afsha', 77.5, 86.0), ('tenth', 85.5, 94.0), ('all', 0, 126)]:
    segs, _ = m.transcribe(pcm(a, b), language='ar')
    out[name] = ' '.join(s.text.strip() for s in segs); print(name, '|', out[name])
json.dump(out, open('sample/pl/ahly/large.json', 'w'), ensure_ascii=False, indent=1)
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0; football-legend.com)'}
for lg in ['caf.champions', 'egy.1']:
    try:
        t = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/teams', headers=UA), timeout=30).read())
        for x in t['sports'][0]['leagues'][0]['teams']:
            tm = x['team']
            if 'ahly' in tm['displayName'].lower():
                print(lg, tm['id'], tm['displayName'], [l['href'] for l in tm.get('logos', [])][:2])
                for i, l in enumerate(tm.get('logos', [])[:2]):
                    open(f'sample/pl/ahly/crest-{tm["id"]}-{i}.png', 'wb').write(urllib.request.urlopen(urllib.request.Request(l['href'], headers=UA), timeout=30).read())
    except Exception as e:
        print(lg, 'failed', e)
