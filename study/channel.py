# Study of a reference Shorts channel (owner's request, 2026-11-21): list with views, RSS publish times and
# descriptions, and thumbnails of the top Shorts. Read-only research for our own original reels.
import json, os, re, subprocess, sys, urllib.request
import xml.etree.ElementTree as ET
CH, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def sh(c):
    return subprocess.run(c, shell=True, capture_output=True, text=True)


r = sh(f"yt-dlp --flat-playlist -J '{CH}/shorts'")
lst = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else {}
ents = [e for e in lst.get("entries", []) if e.get("id")]
summary = {"channel": lst.get("channel") or lst.get("title"), "channel_id": lst.get("channel_id") or lst.get("id"),
           "listed": len(ents), "list_err": r.stderr[-1500:] if r.returncode else "",
           "all": [{"id": e["id"], "title": e.get("title"), "views": e.get("view_count")} for e in ents]}
cid = summary["channel_id"]
try:
    if not cid or not str(cid).startswith("UC"):
        html = urllib.request.urlopen(urllib.request.Request(CH, headers={"User-Agent": "Mozilla/5.0"}),
                                      timeout=30).read().decode("utf-8", "ignore")
        m = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html)
        cid = m.group(1) if m else cid
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
          "media": "http://search.yahoo.com/mrss/"}
    root = ET.fromstring(urllib.request.urlopen(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}",
                                                timeout=30).read())
    summary["rss"] = []
    for e in root.findall("a:entry", ns):
        st = e.find("media:group/media:community/media:statistics", ns)
        summary["rss"].append({"id": e.findtext("yt:videoId", namespaces=ns), "title": e.findtext("a:title", namespaces=ns),
                               "published": e.findtext("a:published", namespaces=ns),
                               "views": int(st.get("views")) if st is not None and st.get("views") else None,
                               "description": (e.findtext("media:group/media:description", namespaces=ns) or "")[:500]})
except Exception as ex:
    summary["rss_err"] = str(ex)[:300]
top = sorted(ents, key=lambda e: -(e.get("view_count") or 0))[:24]
os.makedirs(f"{OUT}/thumbs", exist_ok=True)
for i, a in enumerate(top):
    for q in ("oardefault", "hq720", "hqdefault"):
        if sh(f"curl -sSfL -o {OUT}/thumbs/{i:02d}.jpg https://i.ytimg.com/vi/{a['id']}/{q}.jpg").returncode == 0:
            break
sh(f"ffmpeg -v error -y -pattern_type glob -i '{OUT}/thumbs/*.jpg' -vf 'scale=270:480:force_original_aspect_ratio="
   f"decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2,tile=8x3' -frames:v 1 {OUT}/thumbs_sheet.jpg")
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1)
print(summary["channel"], summary["listed"])
