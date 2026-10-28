# «مسيرة اللاعب» (the player's career videos)

Made by hand in a Claude session, two a day from `queue.txt` (owner, 2026-10-28). The site's server only reads the
voice (Gemini, through `/v2/reels/voice`) and posts what the owner picks on Telegram («مسيرة» / `/career`).

1. **Facts.** On the `voice-sample` branch, `sample/players.txt` (`name|commons search;search`) → `sample/research.py`
   saves FotMob's player data (clubs, seasons, trophies, national team) and the club logos, and Commons photo
   candidates. Check the current club and every record against the clubs' and leagues' own sites before writing.
2. **Voice.** `sample/career/<slug>/voice.txt`: one line per scene, MSA, numbers in words. Pushing it makes
   `voice.mp3` read in ONE call (Puck, ar-EG, the English direction for the Egyptian accent) and `voice.json`
   (whisper, with word timings). `photos.txt` (Commons file titles) → `ph/NN.jpg` with `credits.json`; the first
   photo is the hook.
3. **Page.** `players/<slug>.py` (name, badges, logos, scenes) → `python3 build.py players/<slug>.py work/<slug>`
   over `template.html` (Kane's approved design). `preview.cjs` makes stills to check every scene.
4. **Timing.** `align.py voice.txt voice.json` finds each line's start; fix by hand where whisper mishears, into
   `players/<slug>.timing.json` (`{starts, end}`). Captions are `players/<slug>.caps.txt` (digits).
5. **Render.** `run.sh <slug>`: frames at 30 fps, then MP4 at 24 fps, CRF 30, AAC 96k, music at 0.13.
6. **Publish.** Copy to `videos/<slug>-N.mp4` and add an entry to `videos/index.json`
   (`id: path-<slug>-N`, video, seconds, player, top, caption). The server announces it on Telegram once; the owner
   watches it there and presses 🚀 to post it (Facebook, Instagram, then YouTube).
