import urllib.parse
# One-off (2026-10-30): what Google News carries from Fabrizio Romano in the last two days.
import re, html, urllib.request
for q in ['Fabrizio Romano when:2d', 'فابريزيو رومانو when:2d']:
    hl = '&hl=ar&gl=EG&ceid=EG:ar' if 'ف' in q else '&hl=en-GB&gl=GB&ceid=GB:en'
    x = urllib.request.urlopen(urllib.request.Request('https://news.google.com/rss/search?q=' + urllib.parse.quote(q) + hl, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode()
    items = re.findall(r'<item><title>(.*?)</title>.*?<pubDate>(.*?)</pubDate>.*?<source[^>]*>(.*?)</source>', x)
    print('==', q, len(items))
    for t, d, s in items[:40]: print(' ', d[5:22], '|', s, '|', html.unescape(t)[:170])
