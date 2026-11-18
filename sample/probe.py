# One-off (2026-11-18): the comedy reel in English, step 2: a line at a time in Fenrir (en-GB, the FB Legends voice),
# each checked by whisper (what it really says).
import json, os, subprocess, sys, time, urllib.request, urllib.parse
K = os.environ['REELS_KEY']
lines = json.load(open('sample/yt/dub/en.json'))
for i, (s, e, t) in enumerate(lines):
    for k in range(4):
        u = 'https://api.football-legend.com/v2/reels/voice?' + urllib.parse.urlencode({'key': K, 'voice': 'Fenrir', 'lang': 'en-GB', 'text': t})
        try:
            d = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'fl-probe'}), timeout=120).read()
            open('/tmp/v.wav', 'wb').write(d); subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', '/tmp/v.wav', '-b:a', '160k', f'sample/yt/dub/en-{i:02d}.mp3'], check=True)
            print('PROBE line', i, 'ok'); break
        except Exception as x:
            print('PROBE line', i, 'try', k, x); time.sleep(20)
    time.sleep(8)
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'faster-whisper'], check=True)
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
for i in range(len(lines)):
    f = f'sample/yt/dub/en-{i:02d}.mp3'
    if not os.path.exists(f): continue
    d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip()
    segs, _ = m.transcribe(f, language='en')
    print('PROBE heard', i, d, ' '.join(x.text.strip() for x in segs))
