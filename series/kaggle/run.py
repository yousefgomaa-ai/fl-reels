# One-off test (owner, 2026-11-12): Wan 2.1 1.3B made a 5 s shot in 39 min on one T4 (fp16, efficient attention).
# Now: both T4s at once, and the CausVid LoRA (few steps, no CFG) to see how fast a shot can get.
import subprocess, time, json, os, sys
subprocess.run("pip install -q -U diffusers transformers accelerate sentencepiece imageio imageio-ffmpeg ftfy peft", shell=True)
import torch
n = torch.cuda.device_count()
log = {"gpus": [torch.cuda.get_device_name(i) for i in range(n)]}
print(log, flush=True)
subprocess.run("curl -sSfL -o causvid.safetensors https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan21_CausVid_bidirect2_T2V_1_3B_lora_rank32.safetensors", shell=True)
SHOTS = [
    ("emma", "Cinematic thriller shot. A young woman with auburn hair in a grey cardigan stands in a dark hallway at night, "
             "her back pressed against the front door. She slowly turns her head toward the door, breathing fast, eyes wide with fear, "
             "her phone screen lighting her face. Subtle handheld camera, moody low-key lighting, realistic."),
    ("mark", "Cinematic thriller shot at night. A tall man in his forties with a short dark beard and a black wool coat stands on a front porch "
             "under a single porch light. He slowly raises a house key toward the camera and smiles a cold, knowing smile. "
             "Slow push-in camera, moody low-key lighting, realistic."),
]
W = r'''
import sys, time, json, torch, os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
from diffusers import AutoencoderKLWan, WanPipeline, UniPCMultistepScheduler
from diffusers.utils import export_to_video
name, prompt = sys.argv[1], sys.argv[2]
mid = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
pipe = WanPipeline.from_pretrained(mid, vae=vae, torch_dtype=torch.float16)
pipe.transformer.set_attention_backend("_native_efficient")
out = {"name": name}
try:
    pipe.load_lora_weights("causvid.safetensors", adapter_name="causvid"); pipe.set_adapters(["causvid"], [1.0])
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=8.0)
    steps, cfg = 8, 1.0; out["lora"] = True
except Exception as e:
    out["lora_error"] = str(e)[-600:]; steps, cfg = 30, 5.0
pipe.enable_model_cpu_offload()
t = time.time()
v = pipe(prompt=prompt, negative_prompt="worst quality, blurry, jittery, distorted, deformed face, extra fingers, text, watermark",
         height=832, width=480, num_frames=81, guidance_scale=cfg, num_inference_steps=steps,
         generator=torch.Generator().manual_seed(7)).frames[0]
out["seconds"] = round(time.time() - t); out["steps"] = steps
export_to_video(v, name + ".mp4", fps=16)
json.dump(out, open(name + ".json", "w"))
'''
open("shot.py", "w").write(W)
t = time.time()
procs = []
for i, (name, prompt) in enumerate(SHOTS):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(i % max(n, 1)))
    procs.append(subprocess.Popen([sys.executable, "shot.py", name, prompt], env=env,
                                  stdout=open(name + ".out", "w"), stderr=subprocess.STDOUT))
for p in procs:
    p.wait()
log["wall_seconds_both"] = round(time.time() - t)
for name, _ in SHOTS:
    try:
        log[name] = json.load(open(name + ".json"))
    except Exception:
        log[name + "_tail"] = open(name + ".out").read()[-1500:]
print(json.dumps(log), flush=True)
json.dump(log, open("log.json", "w"), indent=1)
for f in os.listdir("."):
    if f.endswith((".out", ".safetensors")) or f == "shot.py":
        os.remove(f)
