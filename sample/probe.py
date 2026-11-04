# One-off (2026-11-04): Al Ahly history video, large-v3 on four doubtful spots of the new reading, each on its own.
import json, os, subprocess
import numpy as np
from faster_whisper import WhisperModel
vm = 'sample/career/yt-ahly/voice.mp3'
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
def pcm(a, b): return np.frombuffer(subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(a), '-to', str(b), '-i', vm, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout, np.float32)
out = []
for name, a, b in [('sixth', 55.0, 61.2), ('one-year', 66.0, 71.2), ('afsha', 82.0, 90.9), ('tenth', 90.3, 98.9), ('tenth-tight', 95.5, 98.9), ('seventeen', 115.0, 119.8)]:
    for run in range(2):
        segs, _ = m.transcribe(pcm(a, b), language='ar', beam_size=5 + run * 5)
        t = ' '.join(s.text.strip() for s in segs); out.append([name, run, t]); print(name, run, '|', t)
os.makedirs('sample/pl/ahly', exist_ok=True)
json.dump(out, open('sample/pl/ahly/large3.json', 'w'), ensure_ascii=False, indent=1)
