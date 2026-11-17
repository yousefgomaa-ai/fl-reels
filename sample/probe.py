# One-off (2026-11-17): the owner's comedy reel dubbed into English. Step 1: what the Arabic voice says (whisper, word
# times) and the voice taken out of the soundtrack (demucs), so the English voice goes over the same music and sounds.
import subprocess, json, sys
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'faster-whisper', 'demucs', 'soundfile'], check=True)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'sample/yt/dub/in.m4a', '-ac', '2', '-ar', '44100', '/tmp/in.wav'], check=True)
from faster_whisper import WhisperModel
for name in ['large-v3']:
    m = WhisperModel(name, device='cpu', compute_type='int8')
    segs, info = m.transcribe('/tmp/in.wav', language='ar', word_timestamps=True, vad_filter=True)
    out = [{'s': round(s.start, 2), 'e': round(s.end, 2), 't': s.text.strip()} for s in segs]
    for o in out: print('PROBE', name, f"{o['s']:6.2f}-{o['e']:6.2f}", o['t'])
    json.dump(out, open('sample/yt/dub/ar.json', 'w'), ensure_ascii=False, indent=1)
r = subprocess.run([sys.executable, '-m', 'demucs', '--two-stems=vocals', '-n', 'htdemucs', '-o', '/tmp/sep', '/tmp/in.wav'], capture_output=True, text=True)
print('PROBE demucs', r.returncode, r.stderr[-400:])
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', '/tmp/sep/htdemucs/in/no_vocals.wav', '-b:a', '192k', 'sample/yt/dub/bed.mp3'])
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', '/tmp/sep/htdemucs/in/vocals.wav', '-b:a', '128k', 'sample/yt/dub/vocals.mp3'])
