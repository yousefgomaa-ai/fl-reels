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
    # Run 2 (2026-11-13): 4 steps took 42 s but the job was killed (host RAM) at the decode. Now the prompts are encoded
    # first, the text encoder and the transformer are dropped, and only then the VAE decodes on the GPU.
    import gc
    t0 = time.time()
    vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanPipeline.from_pretrained(mid, vae=vae, torch_dtype=torch.float16)
    pipe.text_encoder.to("cuda:0")
    emb = {}
    with torch.no_grad():
        for name, p in shots:
            pe, ne = pipe.encode_prompt(prompt=p, negative_prompt=NEG, do_classifier_free_guidance=cfg > 1, device="cuda:0", dtype=torch.float16)
            emb[name] = (pe.cpu(), ne.cpu() if ne is not None else None)
    pipe.text_encoder = None; gc.collect(); torch.cuda.empty_cache()
    pipe.transformer.to("cuda:0"); pipe.transformer.set_attention_backend("_native_efficient")
    log[tag + "_load"] = round(time.time() - t0)
    lat = {}
    for name, _ in shots:
        t = time.time()
        pe, ne = emb[name]
        with torch.no_grad():
            lat[name] = pipe(prompt_embeds=pe.to("cuda:0"), negative_prompt_embeds=ne.to("cuda:0") if ne is not None else None,
                             height=h, width=w, num_frames=frames, guidance_scale=cfg, num_inference_steps=steps,
                             generator=torch.Generator().manual_seed(11), output_type="latent").frames.cpu()
        log[f"{tag}_{name}_sample_seconds"] = round(time.time() - t)
    pipe.transformer = None; gc.collect(); torch.cuda.empty_cache()
    vae = pipe.vae.to("cuda:0"); vae.enable_tiling()
    mean = torch.tensor(vae.config.latents_mean).view(1, vae.config.z_dim, 1, 1, 1).to("cuda:0")
    std = 1.0 / torch.tensor(vae.config.latents_std).view(1, vae.config.z_dim, 1, 1, 1).to("cuda:0")
    for name, _ in shots:
        t = time.time()
        with torch.no_grad():
            x = lat[name].to("cuda:0", torch.float32) / std + mean
            v = vae.decode(x, return_dict=False)[0]
            v = pipe.video_processor.postprocess_video(v, output_type="np")[0]
        export_to_video(v, f"{tag}_{name}.mp4", fps=fps)
        log[f"{tag}_{name}_decode_seconds"] = round(time.time() - t)
        json.dump(log, open("log.json", "w"), indent=1); print(log, flush=True)
    del pipe, vae; gc.collect(); torch.cuda.empty_cache()

for args in (("FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers", "fast", [("emma", EMMA), ("mark", MARK)], 832, 480, 81, 4, 1.0, 16),
             ("Wan-AI/Wan2.2-TI2V-5B-Diffusers", "base", [("emma", EMMA)], 832, 480, 81, 20, 5.0, 16)):
    try:
        make(*args)
    except Exception:
        log[args[1] + "_error"] = traceback.format_exc()[-1500:]
        json.dump(log, open("log.json", "w"), indent=1)
        torch.cuda.empty_cache()
json.dump(log, open("log.json", "w"), indent=1)
