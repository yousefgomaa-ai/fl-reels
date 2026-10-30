# One-off (2026-10-30): whisper large-v3 on the doubtful numbers of the YouTube samples' voices.
import subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
for f, a, b in [('yt-history', 27.0, 38.3), ('yt-history', 43.2, 49.7), ('yt-preview', 33.2, 41.4), ('yt-preview', 65.2, 70.4), ('yt-preview', 24.0, 27.7)]:
    pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(a), '-to', str(b), '-i', f'sample/career/{f}/voice.mp3', '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
    segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), language='ar', beam_size=5)
    print(f, a, b, '|', ' '.join(s.text.strip() for s in segs))
