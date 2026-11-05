# One-off (2026-11-05): career videos, large-v3 on Lautaro's new reading and Vitinha's.
import os, subprocess
import numpy as np
from faster_whisper import WhisperModel
os.makedirs('sample/pl', exist_ok=True)
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
with open('sample/pl/career-large2.txt', 'w') as f:
    for p in ['lautaro', 'vitinha']:
        vm = f'sample/career/{p}/voice.mp3'
        if not os.path.exists(vm): f.write(f'{p}: no voice\n'); continue
        pcm = np.frombuffer(subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', vm, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout, np.float32)
        for s in m.transcribe(pcm, language='ar')[0]: f.write(f'{p} {s.start:.2f} {s.text.strip()}\n')
print(open('sample/pl/career-large2.txt').read())
