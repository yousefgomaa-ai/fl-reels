# One-off (2026-10-31): whisper large-v3 on Raphinha's 34 goals.
import subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', '43.1', '-to', '51.2', '-i', 'sample/career/raphinha/voice.mp3', '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), language='ar', beam_size=5, word_timestamps=True)
for s in segs:
    print(s.text.strip()); print([(round(w.start + 43.1, 2), w.word) for w in s.words])
