# Satisfying sample on Kaggle's free T4s (owner, 2026-11-18): Wan 2.2 TI2V 5B (FastWan, 4 steps), the same recipe as
# the series shots: fp16 + efficient attention, sample on GPU 0, drop the transformer, decode on both GPUs.
import subprocess, time, json, os, sys, urllib.request
SHA = "EP_SHA"
W = "/kaggle/working"
os.makedirs(f"{W}/clips", exist_ok=True)
log = {"t0": time.time()}
def save():
    json.dump(log, open(f"{W}/log.json", "w"), indent=1)
def sh(c, key=None):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    print(c[:140], r.returncode, r.stdout[-600:], r.stderr[-2500:], flush=True)
    if key:
        log[key] = {"rc": r.returncode, "err": r.stderr[-1500:] if r.returncode else ""}; save()
    return r
J = json.load(urllib.request.urlopen(f"https://raw.githubusercontent.com/yousefgomaa-ai/fl-reels/{SHA}/sat/sample.json"))
sh("pip uninstall -y -q torchao; pip install -q -U diffusers transformers accelerate sentencepiece imageio imageio-ffmpeg ftfy peft")
json.dump({"shots": [[c["id"], c["v"] + " " + J["style"] + ".", 300 + i] for i, c in enumerate(J["clips"])], "W": W}, open("/tmp/wan_job.json", "w"))
open("/tmp/wan.py", "w").write(r'''
import json, os, gc, threading, torch
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
        export_to_video(x, f"{W}/clips/{sid}.mp4", fps=16)
        print("decoded", sid, g, flush=True)
ths = [threading.Thread(target=dec, args=(g,)) for g in range(n)]
[th.start() for th in ths]; [th.join() for th in ths]
''')
sh(f"{sys.executable} /tmp/wan.py", "wan_run")
log["made"] = sorted(os.listdir(f"{W}/clips"))
log["total_seconds"] = round(time.time() - log.pop("t0")); save()
