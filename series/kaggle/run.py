# One-off test (owner, 2026-11-12): can Kaggle's free GPU make real moving shots? Times LTX-Video and Wan 2.1 1.3B.
import subprocess, time, json, os, traceback
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
subprocess.run("pip install -q -U diffusers transformers accelerate sentencepiece imageio imageio-ffmpeg ftfy", shell=True)
import torch
from diffusers.utils import export_to_video, load_image
log = {"gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none",
       "bf16": torch.cuda.is_available() and torch.cuda.is_bf16_supported()}
print(log, flush=True)
IMG = "https://raw.githubusercontent.com/yousefgomaa-ai/fl-reels/claude/series-sample/series/frames/img09.jpg"
PROMPT = ("Cinematic thriller shot. A young woman with auburn hair in a grey cardigan stands in a dark hallway at night, "
          "her back pressed against the front door. She slowly turns her head toward the door, breathing fast, eyes wide with fear, "
          "her phone screen lighting her face. Subtle handheld camera, moody low-key lighting, realistic.")
NEG = "worst quality, blurry, jittery, distorted, deformed face, extra fingers, text, watermark"

def eff(pipe):
    try:
        pipe.transformer.set_attention_backend("_native_efficient"); log.setdefault("attn", "_native_efficient")
    except Exception as e:
        log["attn_error"] = str(e)[:300]

def ltx(dt=torch.bfloat16):
    from diffusers import LTXImageToVideoPipeline
    pipe = LTXImageToVideoPipeline.from_pretrained("Lightricks/LTX-Video", torch_dtype=dt)
    eff(pipe); pipe.enable_model_cpu_offload(); pipe.vae.enable_tiling()
    img = load_image(IMG).resize((512, 896))
    t = time.time()
    v = pipe(image=img, prompt=PROMPT, negative_prompt=NEG, width=512, height=896, num_frames=121,
             num_inference_steps=40, generator=torch.Generator().manual_seed(7)).frames[0]
    log["ltx_seconds"] = round(time.time() - t)
    export_to_video(v, "ltx.mp4", fps=24)

def wan(dt=torch.bfloat16):
    from diffusers import AutoencoderKLWan, WanPipeline
    mid = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
    vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanPipeline.from_pretrained(mid, vae=vae, torch_dtype=dt)
    eff(pipe); pipe.enable_model_cpu_offload()
    t = time.time()
    v = pipe(prompt=PROMPT, negative_prompt=NEG, height=832, width=480, num_frames=81, guidance_scale=5.0,
             num_inference_steps=30, generator=torch.Generator().manual_seed(7)).frames[0]
    log["wan_seconds"] = round(time.time() - t)
    export_to_video(v, "wan.mp4", fps=16)

for name, fn in (("ltx", ltx), ("wan", wan)):
    for dt in (torch.bfloat16, torch.float16):
        try:
            fn(dt); log[name + "_dtype"] = str(dt); break
        except Exception as e:
            log[name + "_error_" + str(dt)[-4:]] = traceback.format_exc()[-800:]
            torch.cuda.empty_cache()
    print(json.dumps(log), flush=True)
    torch.cuda.empty_cache()
json.dump(log, open("log.json", "w"), indent=1)
