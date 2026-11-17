# One-off trial (owner, 2026-11-17): find football Shorts that went viral (no match footage), then run OpenMontage's
# VideoAnalyzer on each (scenes, pacing, keyframes, transcript; local, no API key, no Gemini).
import json, subprocess, sys, re, os
sys.path.insert(0, 'OpenMontage')
SKIP = re.compile(r'ملخص|اهداف|أهداف|هدف|لقطات|مباراة كاملة|بث مباشر|highlights?|goals?|extended|live|vs\.?\s', re.I)
found = {}
for q in ['كرة القدم #shorts', 'محمد صلاح #shorts', 'الاهلي #shorts', 'ميسي رونالدو #shorts', 'football facts #shorts']:
    out = subprocess.run(['yt-dlp', '--flat-playlist', '-J', f'ytsearch15:{q}'], capture_output=True, text=True, timeout=180)
    print(q, 'exit', out.returncode, out.stderr[-300:])
    try: items = json.loads(out.stdout).get('entries', [])
    except Exception: items = []
    for e in items:
        t = e.get('title') or ''
        if SKIP.search(t) or (e.get('duration') or 0) > 90: continue
        found[e['id']] = {'id': e['id'], 'title': t, 'views': e.get('view_count'), 'dur': e.get('duration'), 'channel': e.get('channel')}
top = sorted(found.values(), key=lambda x: -(x['views'] or 0))[:12]
print(json.dumps(top, ensure_ascii=False, indent=1))
from tools.analysis.video_analyzer import VideoAnalyzer
res = []
for v in top[:2]:
    r = VideoAnalyzer().execute({'source': f"https://www.youtube.com/shorts/{v['id']}", 'analysis_depth': 'standard', 'max_keyframes': 8, 'output_dir': f"probe/out/{v['id']}"})
    print(v['id'], 'success', r.success, r.error)
    res.append({**v, 'ok': r.success, 'brief': r.data})
json.dump({'top': top, 'analysed': res}, open('probe/result.json', 'w'), ensure_ascii=False, indent=1, default=str)
