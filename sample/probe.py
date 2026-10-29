# One-off check (2026-10-29): the doubtful bits of the career voices read again by a bigger whisper model.
import subprocess
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
for f, a, b in (('hakimi', 66.5, 75.5), ('hakimi', 89.8, 93.9), ('mbappe', 35.5, 41.4), ('mbappe', 91.0, 96.5)):
    pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(a), '-t', str(b - a), '-i', f'sample/career/{f}/voice.mp3', '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
    for beam in (5,):
        segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), language='ar', beam_size=beam)
        print('CHECK', f, a, b, '|', ' '.join(s.text.strip() for s in segs))
