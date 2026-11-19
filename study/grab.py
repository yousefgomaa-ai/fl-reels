# Study of a YouTube Shorts channel (owner, 2026-11-19): metadata, a frame sheet per Short (one frame every 0.5 s),
# the audio loudness over time and auto captions when YouTube has them. Read-only research; nothing is re-uploaded.
import glob, json, os, subprocess, sys
CH = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
def sh(c):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    return r
r = sh(f"yt-dlp --flat-playlist -J '{CH}/shorts'")
lst = json.loads(r.stdout) if r.returncode == 0 else {}
ids = [e["id"] for e in lst.get("entries", [])]
summary = {"listed": len(ids), "list_err": r.stderr[-1500:] if r.returncode else "", "items": []}
for i, vid in enumerate(ids[:40]):
    d = f"{OUT}/{i:02d}_{vid}"
    os.makedirs(d, exist_ok=True)
    url = f"https://www.youtube.com/shorts/{vid}"
    m = sh(f"yt-dlp -J --skip-download '{url}'")
    info = json.loads(m.stdout) if m.returncode == 0 else {}
    item = {k: info.get(k) for k in ("id", "title", "description", "duration", "view_count", "like_count",
                                     "comment_count", "upload_date", "width", "height", "fps", "tags")}
    item["meta_err"] = m.stderr[-600:] if m.returncode else ""
    sh(f"curl -sSfL -o {d}/thumb.jpg https://i.ytimg.com/vi/{vid}/hq720.jpg || curl -sSfL -o {d}/thumb.jpg https://i.ytimg.com/vi/{vid}/hqdefault.jpg")
    v = sh(f"yt-dlp -f 'bv*[height<=640]+ba/b[height<=640]/worst' --merge-output-format mp4 "
           f"--write-auto-subs --sub-langs 'en.*,ar.*' --sub-format vtt -o '{d}/v.%(ext)s' '{url}'")
    item["dl_err"] = v.stderr[-600:] if v.returncode else ""
    mp4 = (glob.glob(f"{d}/v.mp4") + glob.glob(f"{d}/v.*mp4") + glob.glob(f"{d}/v.webm"))
    if mp4:
        f = mp4[0]
        sh(f"ffmpeg -v error -y -i '{f}' -vf 'fps=2,scale=160:-2,tile=10x8' -frames:v 1 -q:v 4 {d}/sheet.jpg")
        sh(f"ffmpeg -v error -y -i '{f}' -vf 'fps=2,scale=160:-2,tile=10x8' -q:v 4 -start_number 1 {d}/sheet_%d.jpg")
        a = sh(f"ffmpeg -hide_banner -i '{f}' -af 'astats=metadata=1:reset=22050,ametadata=print:key=lavfi.astats.Overall.RMS_level' -f null - 2>&1 | grep -o 'RMS_level=[-0-9.inf]*' | head -400")
        item["rms_half_s"] = [x.split("=")[1] for x in a.stdout.split()][:120]
        p = sh(f"ffprobe -v error -show_entries stream=codec_type,width,height,r_frame_rate:format=duration -of json '{f}'")
        item["probe"] = json.loads(p.stdout or "{}")
        sh(f"ffmpeg -v error -y -i '{f}' -vn -ac 1 -ar 16000 {d}/a.wav")
        os.remove(f)
    subs = glob.glob(f"{d}/*.vtt")
    item["subs"] = [os.path.basename(s) for s in subs]
    json.dump(item, open(f"{d}/info.json", "w"), indent=1)
    summary["items"].append({"dir": os.path.basename(d), "title": item.get("title"), "views": item.get("view_count"),
                             "dur": item.get("duration"), "date": item.get("upload_date"),
                             "video": bool(mp4), "meta_err": item["meta_err"][:200], "dl_err": item["dl_err"][:200]})
    print(i, vid, item.get("view_count"), bool(mp4), flush=True)
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1)
