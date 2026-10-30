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
