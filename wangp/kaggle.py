# WanGP (github.com/deepbeepmeep/Wan2GP) on Kaggle's free T4, headless: one settings file in, one clip out.
# The T4 has no bf16, so --fp16 and plain SDPA attention; WanGP's GTX 10xx recipe (Python 3.10, torch 2.7.1 cu126)
# is used because Kaggle's driver is older than the CUDA 13 build the main recipe asks for.
import json, os, subprocess, sys, time, urllib.request

SHA = "JOB_SHA"                      # replaced by the workflow with the commit that holds job.json
WANGP_REF = "f4cfc1259215577be9a2ee280c41efbedfb4459a"   # pinned WanGP commit (2026-11-18)
W = "/kaggle/working"
os.makedirs(f"{W}/out", exist_ok=True)
log = {"t0": time.time(), "wangp": WANGP_REF}


def save():
    json.dump(log, open(f"{W}/log.json", "w"), indent=1)


def sh(cmd, key=None, tail=3000):
    t = time.time()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("$", cmd[:200], "->", r.returncode, flush=True)
    print(r.stdout[-tail:], r.stderr[-tail:], flush=True)
    if key:
        log[key] = {"rc": r.returncode, "s": round(time.time() - t), "out": r.stdout[-tail:], "err": r.stderr[-tail:]}
        save()
    return r


job = json.load(urllib.request.urlopen(
    f"https://raw.githubusercontent.com/yousefgomaa-ai/fl-reels/{SHA}/wangp/job.json"))
job.pop("_note", None)
log["job"] = job
sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv", "gpu", 600)

# ---- install
sh("pip install -q uv")
UV = sys.executable + " -m uv"
PY = "/tmp/wgp/bin/python"
sh(f"git clone -q https://github.com/deepbeepmeep/Wan2GP.git /tmp/Wan2GP && cd /tmp/Wan2GP && git checkout -q {WANGP_REF}",
   "clone", 600)
sh(f"{UV} venv /tmp/wgp -p 3.10 && {UV} pip install -p {PY} torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 "
   f"--index-url https://download.pytorch.org/whl/cu126", "torch")
r = sh(f"cd /tmp/Wan2GP && {UV} pip install -p {PY} -r requirements.txt --index-strategy unsafe-best-match", "reqs")
if r.returncode:
    # one bad pin should not sink the rest: install line by line and keep a list of what failed
    failed = []
    for line in open("/tmp/Wan2GP/requirements.txt"):
        pkg = line.split("#")[0].strip()
        if not pkg or pkg.startswith("-"):
            continue
        if subprocess.run(f"{UV} pip install -p {PY} '{pkg}'", shell=True, capture_output=True).returncode:
            failed.append(pkg)
    log["reqs_failed"] = failed
    save()

# ---- generate
json.dump(job, open("/tmp/job.json", "w"))
r = sh(f"cd /tmp/Wan2GP && {PY} wgp.py --process /tmp/job.json --output-dir {W}/out "
       f"--fp16 --attention sdpa --profile 4 --verbose 1", "generate", 8000)
log["outputs"] = sorted(os.listdir(f"{W}/out"))
log["total_s"] = round(time.time() - log.pop("t0"))
save()
print(json.dumps({k: v for k, v in log.items() if k not in ("reqs", "torch")}, indent=1)[-6000:])
