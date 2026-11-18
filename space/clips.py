# Makes the scene clips of the space reel on free Hugging Face ZeroGPU Spaces (owner, 2026-11-19).
# Keyframe: Z-Image-Turbo (720x1280). Motion: Wan 2.2 14B image-to-video. Every finished file is kept, and the run
# stops cleanly when the daily ZeroGPU quota is used up, so the next run continues where this one stopped.
import json, os, shutil, sys, time, traceback
from gradio_client import Client, handle_file

cfg = json.load(open(sys.argv[1]))
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
tok = os.environ.get("HF_TOKEN") or None
logp = f"{out}/log.json"
log = json.load(open(logp)) if os.path.exists(logp) else {}
NEG = ("text, subtitles, watermark, logo, blurry, low quality, jpeg artifacts, static, frozen frame, deformed, "
       "extra limbs, cartoon")


def save():
    json.dump(log, open(logp, "w"), indent=1)


def quota(e):
    s = str(e).lower()
    return any(k in s for k in ("quota", "exceeded", "zerogpu", "too many", "rate limit", "429"))


img_c = vid_c = None
stop = False
for sc in cfg["scenes"]:
    if stop:
        break
    sid = sc["id"]
    png, mp4 = f"{out}/{sid}.png", f"{out}/{sid}.mp4"
    rec = log.setdefault(sid, {})
    try:
        if not os.path.exists(png):
            img_c = img_c or Client(cfg["image_space"], token=tok, verbose=False)
            t = time.time()
            r = img_c.predict(prompt=sc["image"], resolution="720x1280 ( 9:16 )", seed=7, steps=8, shift=3.0,
                              random_seed=False, api_name="/generate")
            g = r[0][0]
            path = g["image"]["path"] if isinstance(g.get("image"), dict) else g["image"]
            shutil.copy(path, png)
            rec["image_s"] = round(time.time() - t)
            save()
            print("image", sid, rec["image_s"], "s", flush=True)
        if not os.path.exists(mp4):
            vid_c = vid_c or Client(cfg["video_space"], token=tok, verbose=False)
            t = time.time()
            for secs in (sc.get("seconds", 4), 3.5):
                try:
                    r = vid_c.predict(input_image=handle_file(png), prompt=sc["motion"], steps=6, negative_prompt=NEG,
                                      duration_seconds=secs, guidance_scale=1, guidance_scale_2=1, seed=7,
                                      randomize_seed=False, api_name="/generate_video")
                    break
                except Exception as e:
                    if quota(e) or secs == 3.5:
                        raise
                    rec["retry_short"] = str(e)[:300]
            v = r[0]
            path = v["video"] if isinstance(v, dict) else v
            shutil.copy(path, mp4)
            rec["video_s"] = round(time.time() - t)
            rec["seconds"] = secs
            save()
            print("video", sid, rec["video_s"], "s", flush=True)
    except Exception as e:
        rec["error"] = str(e)[:800]
        save()
        traceback.print_exc()
        if quota(e):
            log["stopped"] = f"quota at {sid} ({time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())})"
            save()
            stop = True
log["done"] = sorted(f for f in os.listdir(out) if f.endswith(".mp4"))
save()
print(json.dumps(log, indent=1)[-4000:])
