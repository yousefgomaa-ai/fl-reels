# Long YouTube videos (owner, 2026-10-30)

Three kinds, each with its own design (YouTube penalises one template for everything):
- `round.py`: «الجولة بالأرقام», the broadcast-board design (dark purple, neon green).
- `preview.py`: «قبل القمة», the split design in the two clubs' colours.
- `history.py`: «تاريخ نادٍ مع بطولة», the museum design (old paper, gold, serif type, the titles lighting up).

`engine.js` draws one scene per narration line at time t; `render.cjs` takes the frames at 1920x1080, 24 fps;
`make.sh <dir> <music>` makes the MP4. `still.cjs <dir>` gives one still per scene to check by eye.
Fonts are local (`fonts/`): the session's browser cannot load Google Fonts through its proxy.

A video's folder holds `page.html` (from the builder), `voice.mp3` + `voice.json` (one reading, whisper; made on
the `voice-sample` branch like the career videos), `timing.json` (each line's start) → `timeline.json`, `logo/`
and `ph/` (Commons photos with `credits.json`). Check every number of the voice against the script, as for careers.

## The plan agreed with the owner (2026-10-30)

Automatic, before and after every round, for 7 leagues: the Premier League, LaLiga, Serie A, the Bundesliga,
Ligue 1, the Egyptian league (egy.1) and the Saudi league (ksa.1).
- **«قبل القمة»** (`preview.py` design): the round's big match, a day before its kick-off. Picked by the two sides'
  places in the table (lowest sum of ranks), a known derby first (Al Ahly–Zamalek, Al Hilal–Al Nassr, El Clasico,
  the Manchester and Milan derbies, Der Klassiker, Le Classique…).
- **«ملخص الجولة»** (was «الجولة بالأرقام», `round.py` design): once the round's last match is over: every result
  with its scorers, the table's top and bottom, the round's numbers, next round's big games.
- **«تاريخ نادٍ أو منتخب مع بطولة»** (`history.py` design): later, made in the session like the career videos
  (old dates and records need checking on the web).

How:
1. **Data** from the site's own API (`api.football-legend.com`: `/matches?date=`, `/standings?league=`,
   `/match/events`, `/match/h2h`), which has Arabic names and covers the Egyptian and Saudi leagues (ESPN refuses egy.1).
2. **Script** from templates in MSA (no AI writing, so no invented facts), with varied wording; numbers in words.
3. **Voice**: one reading through `/v2/reels/voice` (REELS_KEY), then whisper; every number and year of the script
   is compared with whisper automatically, and a video with a mismatch is held and the owner told, never published.
4. **Render** in a fl-reels workflow (`youtube.yml`, public repository: free minutes), 1920x1080, 24 fps.
5. **Store** the MP4 as a GitHub Release asset (not in git: 14 videos a week of 20-60 MB would bloat the repository).
6. **Approve**: the worker announces each video on Telegram (👁 watch, 🚀 YouTube), like the career videos.
7. **Upload**: the worker streams the release asset to YouTube's resumable upload (the Shorts path keeps the whole
   file in KV, 25 MB at most, too small for long videos), with title, description, chapters and tags.
