# Study of single reference Shorts the owner sent (2026-11-22): title, channel, numbers, thumbnail and YouTube's own
# preview frames (25/50/75 %), and a frame sheet if the video itself can be fetched. Read-only research.
import glob, json, os, subprocess, sys
OUT = "study/links"
IDS = sys.argv[1:]
os.makedirs(OUT, exist_ok=True)
def sh(c):
    return subprocess.run(c, shell=True, capture_output=True, text=True)
summary = []
for vid in IDS:
    d = f"{OUT}/{vid}"
    os.makedirs(d, exist_ok=True)
    url = f"https://www.youtube.com/shorts/{vid}"
    item = {"id": vid}
    o = sh(f"curl -sSfL 'https://www.youtube.com/oembed?url={url}&format=json'")
    try:
        item["oembed"] = json.loads(o.stdout)
    except Exception:
        item["oembed_err"] = o.stderr[-300:]
    m = sh(f"yt-dlp -J --skip-download '{url}'")
    if m.returncode == 0:
        info = json.loads(m.stdout)
        item.update({k: info.get(k) for k in ("title", "channel", "channel_follower_count", "description", "duration",
                                               "view_count", "like_count", "comment_count", "upload_date", "tags")})
    else:
        item["meta_err"] = m.stderr[-400:]
    for name in ("hq720", "hqdefault", "1", "2", "3", "maxres1", "maxres2", "maxres3"):
        sh(f"curl -sSfL -o {d}/{name}.jpg https://i.ytimg.com/vi/{vid}/{name}.jpg")
    v = sh(f"yt-dlp -f 'bv*[height<=640]+ba/b[height<=640]/worst' --merge-output-format mp4 -o '{d}/v.%(ext)s' '{url}'")
    item["dl_err"] = v.stderr[-300:] if v.returncode else ""
    mp4 = glob.glob(f"{d}/v.mp4") + glob.glob(f"{d}/v.webm")
    if mp4:
        sh(f"ffmpeg -v error -y -i '{mp4[0]}' -vf 'fps=2,scale=180:-2,tile=8x6' -frames:v 1 -q:v 4 {d}/sheet.jpg")
        sh(f"ffmpeg -v error -y -i '{mp4[0]}' -vf 'select=eq(n\\,0),scale=540:-2' -frames:v 1 {d}/frame0.jpg")
        sh(f"ffmpeg -v error -y -i '{mp4[0]}' -vf 'fps=4,scale=180:-2,tile=8x8' -q:v 4 {d}/dense_%02d.jpg")
        for sec in (0.5, 1, 2, 3, 5, 8, 12, 16, 20, 25, 30, 40):
            sh(f"ffmpeg -v error -y -ss {sec} -i '{mp4[0]}' -frames:v 1 -vf scale=540:-2 {d}/t{sec:05.1f}.jpg")
        os.remove(mp4[0])
    for f in glob.glob(f"{d}/*.jpg"):
        if os.path.getsize(f) < 2000:
            os.remove(f)
    summary.append(item)
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1, ensure_ascii=False)
