# One-off (2026-11-03): whisper large-v3 on Rodri's City numbers (28, 30, 298) and Bellingham's 35.
import subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
for slug, a, b in (('rodri', 41.9, 49.6), ('bellingham', 42.3, 50.1)):
    pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(a), '-to', str(b), '-i', f'sample/career/{slug}/voice.mp3', '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
    segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), language='ar', beam_size=5, word_timestamps=True)
    for s in segs:
        print('PROBE', slug, a, s.text.strip()); print('WORDS', [(round(w.start + a, 2), w.word) for w in s.words])
