# Reference Short the owner sent (2026-11-25): who made it, and how often / when that channel posts.
# oEmbed -> channel handle; channel id; the public RSS feed (latest 15 uploads with publish times + views);
# yt-dlp --flat-playlist of the channel's Shorts tab (ids, titles, view counts where given). Read-only research.
import json, re, subprocess, sys, urllib.request
import xml.etree.ElementTree as ET
vid = sys.argv[1]
OUT = "study/ref"
import os
os.makedirs(OUT, exist_ok=True)
res = {"video": vid}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()


try:
    if vid.startswith("@"):
        raise StopIteration
    oe = json.loads(get(f"https://www.youtube.com/oembed?url=https://www.youtube.com/shorts/{vid}&format=json"))
    res["oembed"] = oe
    handle = oe["author_url"].rstrip("/").split("/")[-1]
except StopIteration:
    handle = vid
except Exception as e:
    res["oembed_err"] = str(e)[:300]
    handle = None
res["handle"] = handle
cid = None
if handle:
    try:
        html = get(f"https://www.youtube.com/{handle}").decode("utf-8", "ignore")
        m = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html) or re.search(r'channel/(UC[0-9A-Za-z_-]{22})', html)
        cid = m.group(1) if m else None
        m2 = re.search(r'"subscriberCountText":\{"accessibility":\{"accessibilityData":\{"label":"([^"]+)"', html) or \
            re.search(r'([0-9.,]+[KMB]?) subscribers', html)
        res["subscribers_text"] = m2.group(1) if m2 else None
        m3 = re.search(r'"joinedDateText":\{[^}]*?"content":"([^"]+)"', html) or re.search(r'Joined ([A-Z][a-z]{2} [0-9]{1,2}, [0-9]{4})', html)
        res["joined"] = m3.group(1) if m3 else None
        m4 = re.search(r'"viewCountText":"([^"]+)"', html) or re.search(r'([0-9,]+) views"', html)
        res["views_text"] = m4.group(1) if m4 else None
    except Exception as e:
        res["page_err"] = str(e)[:300]
res["channel_id"] = cid
ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "media": "http://search.yahoo.com/mrss/"}
items = []
if cid:
    try:
        root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
        for e in root.findall("a:entry", ns):
            st = e.find("media:group/media:community/media:statistics", ns)
            items.append({"id": e.findtext("yt:videoId", namespaces=ns), "title": e.findtext("a:title", namespaces=ns),
                          "published": e.findtext("a:published", namespaces=ns),
                          "views": int(st.get("views")) if st is not None and st.get("views") else None})
    except Exception as e:
        res["feed_err"] = str(e)[:300]
res["rss"] = items
if handle:
    r = subprocess.run(["yt-dlp", "--flat-playlist", "-J", "--playlist-end", "300", f"https://www.youtube.com/{handle}/shorts"],
                       capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
        res["shorts_tab"] = [{"id": e.get("id"), "title": e.get("title"), "views": e.get("view_count")}
                             for e in j.get("entries", [])]
    except Exception:
        res["shorts_err"] = r.stderr[-400:]
# daily history from public trackers / archives (may be blocked)
if handle:
    h = handle.lstrip("@")
    for name, url in (("socialblade", f"https://socialblade.com/youtube/handle/{h}"),
                      ("socialblade_monthly", f"https://socialblade.com/youtube/handle/{h}/monthly"),
                      ("wayback_cdx", f"http://web.archive.org/cdx/search/cdx?url=youtube.com/@{h}*&output=json&limit=50")):
        try:
            body = get(url).decode("utf-8", "ignore")
            res[name] = body[:200000]
        except Exception as e:
            res[name + "_err"] = str(e)[:300]
json.dump(res, open(f"{OUT}/channel_{vid}.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: res.get(k) for k in ("handle", "channel_id", "subscribers_text")}), len(items),
      len(res.get("shorts_tab", [])))
