# Reads the API of the listed Spaces (no generation, no GPU quota).
import json, os, sys
from gradio_client import Client
tok = os.environ.get("HF_TOKEN") or None
ids = json.load(open(sys.argv[1]))["spaces"]
out = {}
for sid in ids:
    try:
        out[sid] = Client(sid, token=tok, verbose=False).view_api(return_format="dict", print_info=False)
    except Exception as e:
        out[sid] = {"error": str(e)[:400]}
json.dump(out, open(sys.argv[2], "w"), indent=1, default=str)
print({k: (list(v.get("named_endpoints", {})) if "error" not in v else v["error"][:100]) for k, v in out.items()})
