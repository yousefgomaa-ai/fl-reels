# One-off (FB Legends, owner 2026-11-03): each star's first hand-picked Commons photo with its background removed
# (rembg, isnet-general-use), trimmed to the player, for the English poster reels. Output: sample/cut/<slug>.png.
import json, io, sys, time, urllib.request, urllib.parse
from PIL import Image
from rembg import remove, new_session
sess = new_session('isnet-general-use')
items = json.load(open('sample/photos.json'))
for it in items:
    url = 'https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(it['file'].replace(' ', '_')) + '?width=1280'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'FootballLegendsReels/1.0 (https://football-legend.com)'})
        raw = urllib.request.urlopen(req, timeout=60).read()
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        out = remove(im, session=sess, post_process_mask=True)
        bb = out.getchannel('A').point(lambda a: 255 if a > 40 else 0).getbbox()
        if bb: out = out.crop(bb)
        if out.height > 1400: out = out.resize((round(out.width * 1400 / out.height), 1400), Image.LANCZOS)
        out.save(f"sample/cut/{it['slug']}.png", optimize=True)
        print('ok', it['slug'], out.size, flush=True)
    except Exception as e:
        print('FAIL', it['slug'], e, flush=True)
    time.sleep(1)
