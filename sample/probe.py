# One-off (2026-11-01): whisper large-v3 on Lamine Yamal's doubtful numbers (2026, 56, 2031).
import subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
for a, b in ((53.4, 58.2), (66.3, 74.0), (80.6, 84.7)):
    pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(a), '-to', str(b), '-i', 'sample/career/yamal/voice.mp3', '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
    segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), language='ar', beam_size=5, word_timestamps=True)
    for s in segs:
        print('PROBE', a, s.text.strip()); print('WORDS', [(round(w.start + a, 2), w.word) for w in s.words])
