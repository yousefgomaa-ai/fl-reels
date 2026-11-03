# One-off (2026-11-03): whisper large-v3 on Luis Díaz's Bayern numbers (31, 20, 62).
import subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
a, b = 54.4, 61.6
pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(a), '-to', str(b), '-i', 'sample/career/diaz/voice.mp3', '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), language='ar', beam_size=5, word_timestamps=True)
for s in segs:
    print('PROBE', s.text.strip()); print('WORDS', [(round(w.start + a, 2), w.word) for w in s.words])
