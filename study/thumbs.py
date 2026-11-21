# Thumbnails of the reference channel's most-viewed Shorts (owner, 2026-11-21), stitched into one sheet. Read-only.
import json, os, subprocess
d = json.load(open("study/simply/summary.json"))
top = sorted(d["all"], key=lambda a: -(a["views"] or 0))[:24]
os.makedirs("study/simply/thumbs", exist_ok=True)
for i, a in enumerate(top):
    for q in ("oardefault", "hq720", "hqdefault"):
        r = subprocess.run(["curl", "-sSfL", "-o", f"study/simply/thumbs/{i:02d}.jpg",
                            f"https://i.ytimg.com/vi/{a['id']}/{q}.jpg"])
        if r.returncode == 0:
            break
subprocess.run("ffmpeg -v error -y -pattern_type glob -i 'study/simply/thumbs/*.jpg' "
               "-vf 'scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2,tile=8x3' "
               "-frames:v 1 study/simply/thumbs_sheet.jpg", shell=True)
json.dump(top, open("study/simply/thumbs/top.json", "w"), indent=1)
