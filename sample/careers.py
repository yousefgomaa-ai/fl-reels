# «مسيرة اللاعب» (owner, 2026-10-28: two videos a day): for each sample/career/<slug>/ the narration read in ONE call
# (voice.txt -> voice.mp3, whisper's timings in voice.json) and the scene photos from Wikimedia Commons (photos.txt ->
# ph/NN.jpg with credits.json). Only what is missing is made, so pushing a new player's folder makes only his.
import glob, json, os, re, subprocess, time, urllib.parse, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (FootballLegends/1.0; football-legend.com)'}
KEY = urllib.parse.quote(os.environ.get('REELS_KEY', ''), safe='')
STYLE = urllib.parse.quote('Read aloud in a warm, natural Egyptian Arabic accent, like an Egyptian football presenter on TV:', safe='')
model = None
for d in sorted(glob.glob('sample/career/*/')):
    vt, vm, vj = d + 'voice.txt', d + 'voice.mp3', d + 'voice.json'
    # Whisper's word timings place each line's start inside a long segment (Ronaldo's came in nine segments for 17 lines).
    if os.path.exists(vj) and not any('w' in x for x in json.load(open(vj))):
        os.remove(vj)
    if os.path.exists(vt) and not os.path.exists(vm):
        text = '\n\n'.join(l.strip() for l in open(vt) if l.strip())
        body = json.dumps({'text': text}).encode()
        for attempt in range(3):
            try:
                req = urllib.request.Request(f'https://api.football-legend.com/v2/reels/voice?key={KEY}&voice=Puck&lang=ar-EG&style={STYLE}', data=body, headers={'Content-Type': 'application/json', **UA})
                open('/tmp/v.wav', 'wb').write(urllib.request.urlopen(req, timeout=240).read()); break
            except Exception as e:
                print(d, 'voice try', attempt + 1, e); time.sleep(20)
        else:
            continue
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', '/tmp/v.wav', '-b:a', '160k', vm], check=True)
    if os.path.exists(vm) and not os.path.exists(vj):
        import numpy as np
        from faster_whisper import WhisperModel
        model = model or WhisperModel('small', device='cpu', compute_type='int8')
        pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', vm, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
        segs, _ = model.transcribe(np.frombuffer(pcm, np.float32), language='ar', word_timestamps=True)
        out = [{'s': round(s.start, 2), 'e': round(s.end, 2), 't': s.text.strip(), 'w': [[round(w.start, 2), w.word.strip()] for w in (s.words or [])]} for s in segs]
        json.dump(out, open(vj, 'w'), ensure_ascii=False)
        print(d, 'voice', round(len(pcm) / 64000, 1), 's')
        for s in out: print('  ', s['s'], s['t'])
    pt = d + 'photos.txt'
    if os.path.exists(pt) and not os.path.exists(d + 'ph/credits.json'):
        os.makedirs(d + 'ph', exist_ok=True)
        cred = []
        for i, t in enumerate([x.strip() for x in open(pt) if x.strip()]):
            time.sleep(4)
            try:
                q = json.loads(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json',
                    'titles': t, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata', 'iiurlwidth': 1080}), headers=UA), timeout=30).read())
                ii = list(q['query']['pages'].values())[0]['imageinfo'][0]; em = ii.get('extmetadata', {})
                time.sleep(2)
                open(f'{d}ph/{i:02d}.jpg', 'wb').write(urllib.request.urlopen(urllib.request.Request(ii['thumburl'], headers=UA), timeout=60).read())
                cred.append({'n': i, 'title': t, 'artist': re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', '')).strip(), 'license': em.get('LicenseShortName', {}).get('value', '')})
                print(d, i, cred[-1]['artist'], cred[-1]['license'])
            except Exception as e:
                print(d, i, t, 'failed', e)
        json.dump(cred, open(d + 'ph/credits.json', 'w'), ensure_ascii=False, indent=1)
