# Read the public course site of a reference channel (owner's request, 2026-11-24): save the pages' text and links.
import os, re, sys, urllib.request, html
OUT = "study/site"
os.makedirs(OUT, exist_ok=True)
start = sys.argv[1]
seen, queue, report = set(), [start], []
host = re.match(r"https?://[^/]+", start).group(0)
while queue and len(seen) < 8:
    url = queue.pop(0)
    if url in seen:
        continue
    seen.add(url)
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                                     timeout=30).read().decode("utf-8", "ignore")
    except Exception as e:
        report.append(f"## {url}\nERROR {e}\n")
        continue
    links = sorted(set(re.findall(r'href="([^"#]+)"', raw)))
    for l in links:
        full = l if l.startswith("http") else host + "/" + l.lstrip("/")
        if full.startswith(host) and full not in seen and not re.search(r"\.(css|js|png|jpg|svg|ico|woff2?)$", full):
            queue.append(full)
    text = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", raw)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text).strip()
    report.append(f"## {url}\nLINKS: {' '.join(links)[:2000]}\n\n{text[:8000]}\n")
open(f"{OUT}/site.md", "w").write("\n".join(report))
