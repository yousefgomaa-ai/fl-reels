# Bigger free model test (owner, 2026-11-12: Veo-like look without paying): Wan 2.2 TI2V 5B on Kaggle's T4.
# A) FastWan2.2 (few-step distilled; 704x1280 ran out of the T4's memory, so 480x832), B) plain Wan 2.2 5B at 480x832, 20 steps. Same prompts as episode 1.
import subprocess, time, json, os, traceback
subprocess.run("pip uninstall -y -q torchao; pip install -q -U diffusers transformers accelerate sentencepiece imageio imageio-ffmpeg ftfy peft", shell=True)
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torch
from diffusers import AutoencoderKLWan, WanPipeline
from diffusers.utils import export_to_video
log = {"gpus": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]}
EMMA = ("Cinematic thriller film shot, night. Extreme close-up of a 32-year-old woman with long straight auburn hair, pale skin with light freckles "
        "and green eyes, in a grey knit cardigan, her back pressed against the inside of her front door in a dark hallway. Terrified, she whispers "
        "to herself, her lips moving, breathing fast, her phone screen lighting her face. Moody low-key lighting, deep shadows, realistic, 35mm film.")
MARK = ("Cinematic thriller film shot, night. A tall 42-year-old man with short black hair and a short trimmed black beard, sharp jaw, wearing a long "
        "black wool overcoat, stands on a front porch under a single dim porch light. He looks straight at the camera and speaks calmly, his lips moving, "
        "then slowly raises a house key and smiles a cold, menacing smile. Slow push-in, moody low-key lighting, realistic, 35mm film.")
NEG = "bright, overexposed, cartoon, anime, blurry, distorted face, deformed hands, extra fingers, text, watermark, subtitles"
def make(mid, tag, shots, h, w, frames, steps, cfg, fps):
    t0 = time.time()
    vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanPipeline.from_pretrained(mid, vae=vae, torch_dtype=torch.float16)
    pipe.enable_model_cpu_offload()
    pipe.transformer.set_attention_backend("_native_efficient")
    pipe.vae.enable_tiling()
    log[tag + "_load"] = round(time.time() - t0)
    for name, p in shots:
        t = time.time()
        v = pipe(prompt=p, negative_prompt=NEG, height=h, width=w, num_frames=frames, guidance_scale=cfg,
                 num_inference_steps=steps, generator=torch.Generator().manual_seed(11)).frames[0]
        export_to_video(v, f"{tag}_{name}.mp4", fps=fps)
        log[f"{tag}_{name}_seconds"] = round(time.time() - t)
        json.dump(log, open("log.json", "w"), indent=1)
        print(log, flush=True)
    del pipe; torch.cuda.empty_cache()
for args in (("FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers", "fast", [("emma", EMMA), ("mark", MARK)], 832, 480, 81, 4, 1.0, 16),
             ("Wan-AI/Wan2.2-TI2V-5B-Diffusers", "base", [("emma", EMMA)], 832, 480, 81, 20, 5.0, 16)):
    try:
        make(*args)
    except Exception:
        log[args[1] + "_error"] = traceback.format_exc()[-1500:]
        json.dump(log, open("log.json", "w"), indent=1)
        torch.cuda.empty_cache()
json.dump(log, open("log.json", "w"), indent=1)
