# Lists live ZeroGPU Spaces for video/image generation and the API of each (no generation, no GPU quota used).
import json, os, sys, traceback
from huggingface_hub import HfApi
from gradio_client import Client

tok = os.environ.get("HF_TOKEN") or None
api = HfApi(token=tok)
out = {"spaces": [], "who": None}
try:
    out["who"] = bool(api.whoami().get("name"))
except Exception as e:
    out["who"] = f"error: {e}"
seen = set()
for q in ["wan2.2", "wan 2.2", "wan2-2", "wan22", "ltx-2", "flux", "qwen-image", "z-image"]:
    try:
        for s in api.list_spaces(search=q, sort="likes", direction=-1, limit=25, full=True):
            if s.id in seen:
                continue
            seen.add(s.id)
            rt = s.runtime or {}
            hw = getattr(rt, "hardware", None) or (rt.get("hardware") if isinstance(rt, dict) else None)
            stage = getattr(rt, "stage", None) or (rt.get("stage") if isinstance(rt, dict) else None)
            out["spaces"].append({"id": s.id, "likes": s.likes, "q": q, "hw": str(hw), "stage": str(stage)})
    except Exception as e:
        out.setdefault("errors", []).append(f"{q}: {e}")
live = [s for s in out["spaces"] if "zero" in s["hw"].lower() and "RUNNING" in s["stage"].upper()]
live.sort(key=lambda s: -(s["likes"] or 0))
out["live_zero"] = [s["id"] for s in live]
apis = {}
for s in live[:24]:
    try:
        c = Client(s["id"], token=tok, verbose=False)
        apis[s["id"]] = c.view_api(return_format="dict", print_info=False)
    except Exception as e:
        apis[s["id"]] = {"error": str(e)[:300]}
out["apis"] = apis
json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
print(json.dumps(out["live_zero"], indent=1))
