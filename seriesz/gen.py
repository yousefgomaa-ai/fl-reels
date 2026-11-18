# Same-face + talking test for THE LAST TEXT on free Hugging Face ZeroGPU Spaces (owner, 2026-11-19).
#   1. Emma's reference portrait ............ Tongyi-MAI/Z-Image-Turbo
#   2. Emma in new scenes, same face ......... black-forest-labs/FLUX.2-klein-9B (reference image, 4 steps)
#   3. Emma speaking her line ................ multimodalart/ltx2-audio-to-video (picture + voice -> talking video)
# Steps run in order of importance and every finished file is kept; on a quota error the run stops, and the next
# run continues from there.
import json, os, shutil, subprocess, sys, time, traceback
from gradio_client import Client, handle_file

cfg = json.load(open(sys.argv[1]))
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
tok = os.environ.get("HF_TOKEN") or None
logp = f"{out}/log.json"
log = json.load(open(logp)) if os.path.exists(logp) else {}

EMMA = ("a 32-year-old woman with long straight auburn hair, pale skin with light freckles and green eyes, "
        "wearing a grey knit cardigan over a black top")
STYLE = "cinematic thriller film still, night, dark moody low-key lighting, deep shadows, realistic, 35mm film"
REF = (f"Portrait photo of {EMMA}, looking at the camera, neutral expression, soft window light, plain dark "
       f"background, sharp focus on the face, realistic skin, vertical composition")
SHOTS = {
    "bedroom": f"The same woman from the reference image, sitting up in bed in a dark bedroom at night, holding a "
               f"glowing smartphone, the cold screen light on her frightened face, close-up, facing the camera, {STYLE}",
    "doorway": f"The same woman from the reference image, standing behind a half-open front door in a dark hallway at "
               f"night, looking out with suspicion, medium close-up, face clearly visible, {STYLE}",
    "kitchen": f"The same woman from the reference image, sitting at a kitchen table at night, lit by a laptop screen, "
               f"worried, medium shot, {STYLE}",
}
TALK = [("bedroom", "l1", "A frightened woman in a dark bedroom speaks in disbelief, lips moving clearly, subtle head "
                          "movement, the phone light on her face, cinematic"),
        ("doorway", "l2", "A suspicious woman behind a half-open door speaks quietly and firmly, lips moving clearly, "
                          "dark hallway, cinematic")]


def save():
    json.dump(log, open(logp, "w"), indent=1)


def quota(e):
    s = str(e).lower()
    return any(k in s for k in ("quota", "exceeded", "too many", "rate limit", "429"))


def first_path(x):
    while isinstance(x, (list, tuple)):
        x = x[0]
    if isinstance(x, dict):
        x = x.get("image") or x.get("video") or x.get("path") or x
        if isinstance(x, dict):
            x = x.get("path")
    return x


clients = {}


def client(sid):
    if sid not in clients:
        clients[sid] = Client(sid, token=tok, verbose=False)
    return clients[sid]


def step(name, fn):
    if name in log.get("ok", []):
        return True
    t = time.time()
    try:
        fn()
        log.setdefault("ok", []).append(name)
        log[name] = {"s": round(time.time() - t)}
        save()
        print("done", name, log[name], flush=True)
        return True
    except Exception as e:
        log[name] = {"error": str(e)[:800], "s": round(time.time() - t)}
        save()
        traceback.print_exc()
        if quota(e):
            log["stopped"] = f"quota at {name} ({time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())})"
            save()
            sys.exit(0)
        return False


def ref():
    r = client("Tongyi-MAI/Z-Image-Turbo").predict(prompt=REF, resolution="720x1280 ( 9:16 )", seed=11, steps=8,
                                                   shift=3.0, random_seed=False, api_name="/generate")
    shutil.copy(first_path(r[0]), f"{out}/emma_ref.png")


def shot(name):
    def run():
        r = client("black-forest-labs/FLUX.2-klein-9B").predict(
            prompt=SHOTS[name], input_images=[{"image": handle_file(f"{out}/emma_ref.png"), "caption": None}],
            mode_choice="Distilled (4 steps)", seed=21, randomize_seed=False, width=720, height=1280,
            num_inference_steps=4, guidance_scale=1.0, prompt_upsampling=False, api_name="/generate")
        shutil.copy(first_path(r), f"{out}/shot_{name}.png")
    return run


def talk(name, line, prompt):
    def run():
        src = f"{os.path.dirname(sys.argv[1])}/voice/{line}.wav"
        wav = f"{out}/{line}_tight.wav"
        # Edge leaves about a second of silence at each "..."; keep pauses near 0.3 s
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af",
                        "silenceremove=start_periods=1:start_threshold=-40dB:stop_periods=-1:stop_duration=0.3:"
                        "stop_threshold=-40dB:stop_silence=0.15,apad=pad_dur=0.3", wav], check=True)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                                   capture_output=True, text=True).stdout)
        r = client("multimodalart/ltx2-audio-to-video").predict(
            image_path=handle_file(f"{out}/shot_{name}.png"), audio_path=handle_file(wav), prompt=prompt,
            negative_prompt="low quality, worst quality, deformed, distorted face, blurry, static, frozen",
            video_duration=round(dur + 0.2, 1), seed=31, api_name="/generate")
        shutil.copy(first_path(r), f"{out}/talk_{name}.mp4")
        log.setdefault("talk_durations", {})[name] = dur
    return run


# order of importance: one talking shot first, then the second, then the silent same-face shot
if step("ref", ref):
    if step("shot_bedroom", shot("bedroom")):
        step("talk_bedroom", talk("bedroom", "l1", TALK[0][2]))
    if step("shot_doorway", shot("doorway")):
        step("talk_doorway", talk("doorway", "l2", TALK[1][2]))
    step("shot_kitchen", shot("kitchen"))
log["files"] = sorted(os.listdir(out))
save()
print(json.dumps(log, indent=1)[-3000:])
