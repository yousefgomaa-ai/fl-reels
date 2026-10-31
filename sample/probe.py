# One-off (2026-10-31): whisper large-v3 on the doubtful numbers of Dembélé's and Mané's voices.
import subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
for f, a, b in [('dembele', 11.8, 15.7), ('dembele', 20.5, 24.4), ('mane', 44.4, 50.7)]:
    pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(a), '-to', str(b), '-i', f'sample/career/{f}/voice.mp3', '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
    segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), language='ar', beam_size=5)
    print(f, a, b, '|', ' '.join(s.text.strip() for s in segs))
