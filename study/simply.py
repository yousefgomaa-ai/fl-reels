# Study of a reference Shorts channel (owner's request, 2026-11-21): the most-viewed and the latest Shorts,
# a frame sheet per Short, the audio (for analysis only), a spectrogram, loudness over time, captions.
# Read-only research for our own original reels; nothing is re-uploaded anywhere.
import glob, json, os, subprocess, sys
CH, OUT = sys.argv[1], sys.argv[2]
TOP, LATEST = 8, 4
os.makedirs(OUT, exist_ok=True)
YT = "yt-dlp --js-runtimes deno --remote-components ejs:github"


def sh(c):
    return subprocess.run(c, shell=True, capture_output=True, text=True)


r = sh(f"{YT} --flat-playlist -J '{CH}/shorts'")
lst = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else {}
ents = [e for e in lst.get("entries", []) if e.get("id")]
summary = {"channel": lst.get("channel") or lst.get("title"), "listed": len(ents),
           "list_err": r.stderr[-1500:] if r.returncode else "",
           "all": [{"id": e["id"], "title": e.get("title"), "views": e.get("view_count")} for e in ents], "items": []}
by_views = sorted(ents, key=lambda e: -(e.get("view_count") or 0))
pick = []
for e in by_views[:TOP] + ents[:LATEST]:
    if e["id"] not in [p["id"] for p in pick]:
        pick.append(e)
for i, e in enumerate(pick):
    vid = e["id"]
    d = f"{OUT}/{i:02d}_{vid}"
    os.makedirs(d, exist_ok=True)
    url = f"https://www.youtube.com/shorts/{vid}"
    m = sh(f"{YT} -J --skip-download '{url}'")
    info = json.loads(m.stdout) if m.returncode == 0 and m.stdout.strip() else {}
    item = {k: info.get(k) for k in ("id", "title", "description", "duration", "view_count", "like_count",
                                     "comment_count", "upload_date", "tags")}
    item["list_views"] = e.get("view_count")
    item["list_title"] = e.get("title")
    item["meta_err"] = m.stderr[-600:] if m.returncode else ""
    v = sh(f"{YT} -f 'bv*[height<=854]+ba/b' --merge-output-format mp4 --write-auto-subs --sub-langs 'en.*' "
           f"--sub-format vtt -o '{d}/v.%(ext)s' '{url}'")
    item["dl_err"] = v.stderr[-800:] if v.returncode else ""
    mp4 = glob.glob(f"{d}/v.mp4") + glob.glob(f"{d}/v.webm") + glob.glob(f"{d}/v.mkv")
    if mp4:
        f = mp4[0]
        sh(f"ffmpeg -v error -y -i '{f}' -vf 'fps=2,scale=180:-2,tile=10x6' -q:v 4 -start_number 1 {d}/sheet_%d.jpg")
        sh(f"ffmpeg -v error -y -i '{f}' -vn -ac 1 -ar 22050 {d}/audio.wav")
        sh(f"ffmpeg -v error -y -i '{f}' -lavfi 'showspectrumpic=s=1400x500:legend=1:scale=log:fscale=log' {d}/spectrum.png")
        a = sh(f"ffmpeg -hide_banner -i '{f}' -af 'astats=metadata=1:reset=11025,ametadata=print:key=lavfi.astats.Overall.RMS_level' "
               f"-f null - 2>&1 | grep -o 'RMS_level=[-0-9.inf]*'")
        item["rms_quarter_s"] = [x.split("=")[1] for x in a.stdout.split()][:400]
        sh(f"ffmpeg -v error -y -i '{f}' -c:v libx264 -crf 30 -preset fast -vf scale=-2:640 -c:a aac -b:a 96k {d}/small.mp4")
        os.remove(f)
    item["subs"] = [os.path.basename(s) for s in glob.glob(f"{d}/*.vtt")]
    json.dump(item, open(f"{d}/info.json", "w"), indent=1)
    summary["items"].append({"dir": os.path.basename(d), "title": item.get("title") or e.get("title"),
                             "views": item.get("view_count") or e.get("view_count"), "dur": item.get("duration"),
                             "date": item.get("upload_date"), "video": bool(mp4), "dl_err": item["dl_err"][:300]})
    print(i, vid, e.get("view_count"), bool(mp4), flush=True)
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1)
