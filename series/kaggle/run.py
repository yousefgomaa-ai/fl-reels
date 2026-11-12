# One-off test (owner, 2026-11-12). Run 2 lessons: Kaggle's old torchao stops peft loading the LoRA (uninstall it),
# and two processes each loading Wan ran out of RAM: load once, encode the prompts, drop the text encoder,
# then one transformer copy per T4, run in two threads. A LoRA failure now stops the run instead of a 40-minute fallback.
import subprocess, time, json, os, copy, threading, traceback
subprocess.run("pip uninstall -y -q torchao; pip install -q -U diffusers transformers accelerate sentencepiece imageio imageio-ffmpeg ftfy peft", shell=True)
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torch
from diffusers import AutoencoderKLWan, WanPipeline, UniPCMultistepScheduler
from diffusers.utils import export_to_video
n = torch.cuda.device_count()
log = {"gpus": [torch.cuda.get_device_name(i) for i in range(n)]}
subprocess.run("curl -sSfL -o /tmp/causvid.safetensors https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan21_CausVid_bidirect2_T2V_1_3B_lora_rank32.safetensors", shell=True)
SHOTS = [
    ("emma", "Cinematic thriller shot. A young woman with auburn hair in a grey cardigan stands in a dark hallway at night, "
             "her back pressed against the front door. She slowly turns her head toward the door, breathing fast, eyes wide with fear, "
             "her phone screen lighting her face. Subtle handheld camera, moody low-key lighting, realistic."),
    ("mark", "Cinematic thriller shot at night. A tall man in his forties with a short dark beard and a black wool coat stands on a front porch "
             "under a single porch light. He slowly raises a house key toward the camera and smiles a cold, knowing smile. "
             "Slow push-in camera, moody low-key lighting, realistic."),
]
mid = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
t0 = time.time()
try:
    vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanPipeline.from_pretrained(mid, vae=vae, torch_dtype=torch.float16)
    pipe.load_lora_weights("/tmp/causvid.safetensors", adapter_name="causvid")
    pipe.fuse_lora(lora_scale=1.0); pipe.unload_lora_weights()
    log["lora"] = True
    pipe.text_encoder.to("cuda:0")
    embeds = []
    with torch.no_grad():
        for _, p in SHOTS:
            pe, _ = pipe.encode_prompt(prompt=p, do_classifier_free_guidance=False, device="cuda:0", dtype=torch.float16)
            embeds.append(pe.cpu())
    pipe.text_encoder = None; torch.cuda.empty_cache()
    sched = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=8.0)
    pipes = []
    for g in range(max(n, 1)):
        p = WanPipeline(tokenizer=pipe.tokenizer, text_encoder=None, vae=copy.deepcopy(pipe.vae),
                        transformer=copy.deepcopy(pipe.transformer), scheduler=copy.deepcopy(sched)).to(f"cuda:{g}")
        p.transformer.set_attention_backend("_native_efficient")
        p.vae.enable_tiling()
        pipes.append(p)
    del pipe
    log["load_seconds"] = round(time.time() - t0)
except Exception:
    log["setup_error"] = traceback.format_exc()[-1500:]
    json.dump(log, open("log.json", "w"), indent=1); raise SystemExit(1)

def shot(i, name, pe):
    g = i % len(pipes)
    try:
        t = time.time()
        v = pipes[g](prompt_embeds=pe.to(f"cuda:{g}"), height=832, width=480, num_frames=81, guidance_scale=1.0,
                     num_inference_steps=8, generator=torch.Generator().manual_seed(7)).frames[0]
        log[name] = {"gpu": g, "seconds": round(time.time() - t)}
        export_to_video(v, name + ".mp4", fps=16)
    except Exception:
        log[name + "_error"] = traceback.format_exc()[-1200:]

t = time.time()
ths = [threading.Thread(target=shot, args=(i, name, embeds[i])) for i, (name, _) in enumerate(SHOTS)]
for th in ths: th.start()
for th in ths: th.join()
log["wall_seconds_both"] = round(time.time() - t)
log["total_seconds"] = round(time.time() - t0)
print(json.dumps(log), flush=True)
json.dump(log, open("log.json", "w"), indent=1)
