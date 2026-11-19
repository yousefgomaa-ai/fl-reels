# Publish times of a channel's latest videos from its public RSS feed (owner, 2026-11-19). Read-only.
import json, re, subprocess, sys, urllib.request
import xml.etree.ElementTree as ET
handle = sys.argv[1]
out = sys.argv[2]
res = {"handle": handle}
r = subprocess.run(["yt-dlp", "--flat-playlist", "-J", "--playlist-items", "1", f"https://www.youtube.com/{handle}/shorts"],
                   capture_output=True, text=True)
cid = None
try:
    j = json.loads(r.stdout)
    cid = j.get("channel_id") or j.get("id")
except Exception as e:
    res["ytdlp_err"] = (r.stderr or str(e))[-600:]
if not cid or not cid.startswith("UC"):
    try:
        html = urllib.request.urlopen(urllib.request.Request(f"https://www.youtube.com/{handle}",
                                      headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", "ignore")
        m = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html) or re.search(r'channel/(UC[0-9A-Za-z_-]{22})', html)
        cid = m.group(1) if m else cid
    except Exception as e:
        res["page_err"] = str(e)[:300]
res["channel_id"] = cid
ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}
items = []
try:
    xml = urllib.request.urlopen(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", timeout=30).read()
    root = ET.fromstring(xml)
    for e in root.findall("a:entry", ns):
        st = e.find("media:group/media:community/media:statistics", ns)
        items.append({"id": e.findtext("yt:videoId", namespaces=ns), "title": e.findtext("a:title", namespaces=ns),
                      "published": e.findtext("a:published", namespaces=ns),
                      "views": int(st.get("views")) if st is not None and st.get("views") else None})
except Exception as e:
    res["feed_err"] = str(e)[:300]
res["items"] = items
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1)[:4000])
