# Episode v2 on Kaggle's two free T4s (owner, 2026-11-17): acted voices, Wan 2.2 shots, lip-sync on the speaking shots.
# Each tool runs in its own process (and venv where its Python differs) so the 29 GB of RAM is freed between steps.
# Lessons from the tests: fp16 + efficient attention on the T4, drop the text encoder and transformer before the VAE
# decode (RAM), torchao out (peft), LatentSync needs Python 3.10, edge-tts does not work from Kaggle.
import subprocess, time, json, os, sys, urllib.request, shutil
SHA = "EP_SHA"
RAW = f"https://raw.githubusercontent.com/yousefgomaa-ai/fl-reels/{SHA}/series/v2/"
W = "/kaggle/working"
for d in ("voice", "shots", "lip", "src"):
    os.makedirs(f"{W}/{d}", exist_ok=True)
log = {"t0": time.time()}
def save():
    json.dump(log, open(f"{W}/log.json", "w"), indent=1)
def sh(c, key=None):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    print(c[:140], r.returncode, r.stdout[-600:], r.stderr[-2500:], flush=True)
    if key:
        log[key] = {"rc": r.returncode, "err": r.stderr[-1500:] if r.returncode else ""}; save()
    return r
EP = json.load(urllib.request.urlopen(RAW + "ep1.json"))
LINES = [(s["id"], k, l) for s in EP["shots"] for k, l in enumerate(s.get("lines", []))]
for sid, k, l in LINES:
    sh(f"curl -sSfL -o {W}/src/{sid}_{k}.wav {RAW}voice_src/{sid}_{k}.wav")
for who in EP["cast"]:
    sh(f"curl -sSfL -o {W}/src/ref_{who}.wav {RAW}voice_src/ref_{who}.wav")
sh("pip install -q uv")
UV = sys.executable + " -m uv"

# ---------- 1. acted voices: Chatterbox (MIT), each character cloned from one fixed reference ----------
t = time.time()
sh(f"{UV} venv /tmp/cb -p 3.11 && {UV} pip install -p /tmp/cb/bin/python chatterbox-tts", "chatterbox_install")
job = {"lines": [[sid, k, l[0], l[1], l[2] if len(l) > 2 else 0.5] for sid, k, l in LINES], "W": W}
json.dump(job, open("/tmp/cb_job.json", "w"))
open("/tmp/cb.py", "w").write(r'''
import json, torch, torchaudio as ta
from chatterbox.tts import ChatterboxTTS
job = json.load(open("/tmp/cb_job.json")); W = job["W"]
m = ChatterboxTTS.from_pretrained(device="cuda")
for sid, k, who, text, ex in job["lines"]:
    if who == "operator":
        continue
    torch.manual_seed(7)
    wav = m.generate(text, audio_prompt_path=f"{W}/src/ref_{who}.wav", exaggeration=ex, cfg_weight=0.3 if ex >= 0.6 else 0.5)
    ta.save(f"{W}/voice/{sid}_{k}.wav", wav, m.sr)
    print("voice", sid, k, flush=True)
''')
sh("/tmp/cb/bin/python /tmp/cb.py", "chatterbox_run")
for sid, k, l in LINES:  # any line Chatterbox did not make keeps the Edge voice (same character voice, less acting)
    if not os.path.exists(f"{W}/voice/{sid}_{k}.wav"):
        shutil.copy(f"{W}/src/{sid}_{k}.wav", f"{W}/voice/{sid}_{k}.wav")
        log.setdefault("edge_fallback", []).append(f"{sid}_{k}")
log["voice_seconds"] = round(time.time() - t); save()

# ---------- 2. shots: Wan 2.2 TI2V 5B (FastWan, 4 steps), sampled on GPU 0, decoded on both GPUs ----------
t = time.time()
sh("pip uninstall -y -q torchao; pip install -q -U diffusers transformers accelerate sentencepiece imageio imageio-ffmpeg ftfy peft")
def prompt(s):
    p = s["v"]
    for k, v in EP["looks"].items():
        p = p.replace("{" + k + "}", v)
    return p + " " + EP["style"] + "."
json.dump({"shots": [[s["id"], prompt(s), 200 + i] for i, s in enumerate(EP["shots"]) if s.get("v")], "W": W}, open("/tmp/wan_job.json", "w"))
open("/tmp/wan.py", "w").write(r'''
import json, os, gc, time, threading, torch
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
from diffusers import AutoencoderKLWan, WanPipeline
from diffusers.utils import export_to_video
job = json.load(open("/tmp/wan_job.json")); W = job["W"]
mid = "FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers"
vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
pipe = WanPipeline.from_pretrained(mid, vae=vae, torch_dtype=torch.float16)
pipe.text_encoder.to("cuda:0")
emb = {}
with torch.no_grad():
    for sid, p, seed in job["shots"]:
        pe, _ = pipe.encode_prompt(prompt=p, do_classifier_free_guidance=False, device="cuda:0", dtype=torch.float16)
        emb[sid] = pe.cpu()
pipe.text_encoder = None; gc.collect(); torch.cuda.empty_cache()
pipe.transformer.to("cuda:0"); pipe.transformer.set_attention_backend("_native_efficient")
lat = {}
for sid, p, seed in job["shots"]:
    with torch.no_grad():
        lat[sid] = pipe(prompt_embeds=emb[sid].to("cuda:0"), height=832, width=480, num_frames=81, guidance_scale=1.0,
                        num_inference_steps=4, generator=torch.Generator().manual_seed(seed), output_type="latent").frames.cpu()
    print("sampled", sid, flush=True)
pipe.transformer = None; gc.collect(); torch.cuda.empty_cache()
n = torch.cuda.device_count()
vaes = []
for g in range(n):
    v = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32).to(f"cuda:{g}"); v.enable_tiling(); vaes.append(v)
ids = list(lat)
def dec(g):
    v = vaes[g]
    mean = torch.tensor(v.config.latents_mean).view(1, v.config.z_dim, 1, 1, 1).to(f"cuda:{g}")
    std = 1.0 / torch.tensor(v.config.latents_std).view(1, v.config.z_dim, 1, 1, 1).to(f"cuda:{g}")
    for sid in ids[g::n]:
        with torch.no_grad():
            x = v.decode(lat[sid].to(f"cuda:{g}", torch.float32) / std + mean, return_dict=False)[0]
            x = pipe.video_processor.postprocess_video(x, output_type="np")[0]
        export_to_video(x, f"{W}/shots/{sid}.mp4", fps=16)
        print("decoded", sid, g, flush=True)
ths = [threading.Thread(target=dec, args=(g,)) for g in range(n)]
[th.start() for th in ths]; [th.join() for th in ths]
''')
sh(f"{sys.executable} /tmp/wan.py", "wan_run")
log["shots_seconds"] = round(time.time() - t); log["shots_made"] = sorted(os.listdir(f"{W}/shots")); save()

# ---------- 3. lip-sync: LatentSync 1.5 (Apache-2.0) on every speaking shot ----------
t = time.time()
sh(f"{UV} venv /tmp/ls -p 3.10 && git clone -q --depth 1 https://github.com/bytedance/LatentSync /tmp/LatentSync && "
   f"cd /tmp/LatentSync && {UV} pip install -p /tmp/ls/bin/python -r requirements.txt huggingface_hub", "latentsync_install")
sh("cd /tmp/LatentSync && (/tmp/ls/bin/huggingface-cli download ByteDance/LatentSync-1.5 --local-dir checkpoints --exclude '*.git*' || /tmp/ls/bin/hf download ByteDance/LatentSync-1.5 --local-dir checkpoints)")
for s in EP["shots"]:
    if not s.get("lip") or not os.path.exists(f"{W}/shots/{s['id']}.mp4"):
        continue
    sid = s["id"]
    # The speech starts 0.3 s into the shot (as in the edit) and is padded to the whole shot, so the clip keeps its length.
    sh(f"ffmpeg -v error -y -f lavfi -t 0.3 -i anullsrc=r=16000:cl=mono -i {W}/voice/{sid}_0.wav -filter_complex "
       f"\"[1:a]aresample=16000,aformat=channel_layouts=mono[v];[0:a][v]concat=n=2:v=0:a=1,apad=whole_dur=5.1[a]\" -map \"[a]\" /tmp/{sid}_lip.wav")
    tt = time.time()
    sh(f"cd /tmp/LatentSync && /tmp/ls/bin/python -m scripts.inference --unet_config_path configs/unet/stage2.yaml "
       f"--inference_ckpt_path checkpoints/latentsync_unet.pt --inference_steps 20 --guidance_scale 1.5 "
       f"--video_path {W}/shots/{sid}.mp4 --audio_path /tmp/{sid}_lip.wav --video_out_path {W}/lip/{sid}.mp4", f"lip_{sid}")
    log[f"lip_{sid}"]["seconds"] = round(time.time() - tt); save()
log["lip_seconds"] = round(time.time() - t)
log["total_seconds"] = round(time.time() - log.pop("t0"))
save()
