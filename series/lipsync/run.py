# Lip-sync test (owner, 2026-11-12: «ليه الاشخاص مبيتكلموش»): LatentSync 1.5 (ByteDance, Apache-2.0) on Kaggle's T4
# makes the character's mouth follow the voice. Kaggle's Python is 3.13; LatentSync needs 3.10, so it runs in a uv venv.
import subprocess, time, json, os
def sh(c):
    r = subprocess.run(c, shell=True, capture_output=True, text=True); print(c[:120], r.returncode, r.stdout[-400:], r.stderr[-1500:], flush=True); return r
log = {}
t0 = time.time()
sh("curl -LsSf https://astral.sh/uv/install.sh | sh")
UV = os.path.expanduser("~/.local/bin/uv")
sh(f"{UV} venv /tmp/ls -p 3.10")
sh("git clone -q --depth 1 https://github.com/bytedance/LatentSync /tmp/LatentSync")
r = sh(f"cd /tmp/LatentSync && {UV} pip install -p /tmp/ls/bin/python -r requirements.txt huggingface_hub edge-tts")
log["install_rc"] = r.returncode; log["install_err"] = r.stderr[-1200:]
sh("cd /tmp/LatentSync && /tmp/ls/bin/huggingface-cli download ByteDance/LatentSync-1.5 --local-dir checkpoints --exclude '*.git*' || /tmp/ls/bin/hf download ByteDance/LatentSync-1.5 --local-dir checkpoints")
sh("ls -la /tmp/LatentSync/checkpoints /tmp/LatentSync/checkpoints/whisper /tmp/LatentSync/configs/unet")
log["setup_seconds"] = round(time.time() - t0)
RAW = "https://raw.githubusercontent.com/yousefgomaa-ai/fl-reels/claude/series-sample/series/ep1/shots/"
TESTS = [("s20", "en-GB-RyanNeural", "-6%", "Emma? I saw your light. Open up. It's just me."),
         ("s21", "en-US-AriaNeural", "-4%", "I never gave you a key.")]
cfg = "configs/unet/stage2.yaml"
for sid, voice, rate, text in TESTS:
    sh(f"curl -sSfL -o /tmp/{sid}.mp4 {RAW}{sid}.mp4")
    sh(f"/tmp/ls/bin/edge-tts --voice {voice} --rate={rate} --text \"{text}\" --write-media /tmp/{sid}.mp3 && ffmpeg -v error -y -i /tmp/{sid}.mp3 -ar 16000 -ac 1 /tmp/{sid}.wav")
    t = time.time()
    r = sh(f"cd /tmp/LatentSync && /tmp/ls/bin/python -m scripts.inference --unet_config_path {cfg} --inference_ckpt_path checkpoints/latentsync_unet.pt "
           f"--inference_steps 20 --guidance_scale 1.5 --video_path /tmp/{sid}.mp4 --audio_path /tmp/{sid}.wav --video_out_path /kaggle/working/lip_{sid}.mp4")
    log[sid] = {"rc": r.returncode, "seconds": round(time.time() - t), "err": r.stderr[-1500:] if r.returncode else ""}
    json.dump(log, open("/kaggle/working/log.json", "w"), indent=1)
log["total_seconds"] = round(time.time() - t0)
json.dump(log, open("/kaggle/working/log.json", "w"), indent=1)
