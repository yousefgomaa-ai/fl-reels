# Episode shots on Kaggle's two free T4s (owner, 2026-11-12): Wan 2.1 T2V 1.3B + CausVid LoRA, 8 steps, no CFG.
# Learnt in the tests: uninstall torchao (peft refuses Kaggle's old one), load once, one transformer copy per GPU,
# fp16 with the memory-efficient attention (bf16 has no kernel on the T4). ~4 min a shot per GPU.
import subprocess, time, json, os, copy, threading, traceback, queue, urllib.request
subprocess.run("pip uninstall -y -q torchao; pip install -q -U diffusers transformers accelerate sentencepiece imageio imageio-ffmpeg ftfy peft", shell=True)
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torch
from diffusers import AutoencoderKLWan, WanPipeline, UniPCMultistepScheduler
from diffusers.utils import export_to_video
EP = json.load(urllib.request.urlopen("https://raw.githubusercontent.com/yousefgomaa-ai/fl-reels/claude/series-sample/series/ep1.json"))
def prompt(s):
    p = s["v"]
    for k, v in EP["looks"].items():
        p = p.replace("{" + k + "}", v)
    return p + " " + EP["style"] + "."
SHOTS = [(s["id"], prompt(s)) for s in EP["shots"] if s.get("v")]
NEG = "bright, overexposed, cartoon, blurry, distorted face, deformed hands, extra fingers, text, watermark, subtitles"
n = torch.cuda.device_count()
log = {"gpus": [torch.cuda.get_device_name(i) for i in range(n)], "shots": {}}
subprocess.run("curl -sSfL -o /tmp/causvid.safetensors https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan21_CausVid_bidirect2_T2V_1_3B_lora_rank32.safetensors", shell=True)
mid = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
t0 = time.time()
vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
pipe = WanPipeline.from_pretrained(mid, vae=vae, torch_dtype=torch.float16)
pipe.load_lora_weights("/tmp/causvid.safetensors", adapter_name="causvid")
pipe.fuse_lora(lora_scale=1.0); pipe.unload_lora_weights()
pipe.text_encoder.to("cuda:0")
embeds = {}
with torch.no_grad():
    for sid, p in SHOTS:
        pe, _ = pipe.encode_prompt(prompt=p, do_classifier_free_guidance=False, device="cuda:0", dtype=torch.float16)
        embeds[sid] = pe.cpu()
pipe.text_encoder = None; torch.cuda.empty_cache()
sched = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=8.0)
pipes = []
for g in range(max(n, 1)):
    p = WanPipeline(tokenizer=pipe.tokenizer, text_encoder=None, vae=copy.deepcopy(pipe.vae),
                    transformer=copy.deepcopy(pipe.transformer), scheduler=copy.deepcopy(sched)).to(f"cuda:{g}")
    p.transformer.set_attention_backend("_native_efficient"); p.vae.enable_tiling()
    pipes.append(p)
del pipe
log["load_seconds"] = round(time.time() - t0)
q = queue.Queue()
for i, (sid, _) in enumerate(SHOTS):
    q.put((i, sid))
def worker(g):
    while True:
        try:
            i, sid = q.get_nowait()
        except queue.Empty:
            return
        try:
            t = time.time()
            v = pipes[g](prompt_embeds=embeds[sid].to(f"cuda:{g}"), height=832, width=480, num_frames=81, guidance_scale=1.0,
                         num_inference_steps=8, generator=torch.Generator().manual_seed(100 + i)).frames[0]
            export_to_video(v, sid + ".mp4", fps=16)
            log["shots"][sid] = {"gpu": g, "seconds": round(time.time() - t)}
        except Exception:
            log["shots"][sid] = {"error": traceback.format_exc()[-800:]}
        print(sid, log["shots"][sid], flush=True)
ths = [threading.Thread(target=worker, args=(g,)) for g in range(len(pipes))]
for th in ths: th.start()
for th in ths: th.join()
log["total_seconds"] = round(time.time() - t0)
json.dump(log, open("log.json", "w"), indent=1)
