# One-off (2026-11-11): Liverpool history video, large-v3 on «واحد وعشرون» and «الخامس», and the whole reading.
import os, subprocess
import numpy as np
from faster_whisper import WhisperModel
vm = 'sample/career/yt-liverpool/voice.mp3'
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
def pcm(a=None, b=None):
    cmd = ['ffmpeg', '-loglevel', 'error'] + (['-ss', str(a), '-to', str(b)] if a is not None else []) + ['-i', vm, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)
with open('sample/pl/lfc/large.txt', 'w') as f:
    for name, a, b in [('21', 49.0, 54.6), ('fifth', 69.6, 76.2)]:
        for beam in (5, 10):
            t = ' '.join(s.text.strip() for s in m.transcribe(pcm(a, b), language='ar', beam_size=beam)[0]); f.write(f'{name} b{beam} | {t}\n')
    for s in m.transcribe(pcm(), language='ar')[0]: f.write(f'all {s.start:.2f} {s.text.strip()}\n')
print(open('sample/pl/lfc/large.txt').read())
