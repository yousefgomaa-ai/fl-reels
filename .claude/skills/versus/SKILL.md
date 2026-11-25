---
name: versus
description: Make a "X vs Y vs Z: who makes it?" Two Paths reel from a short JSON config with the versus.py engine (night lanes, following cameras, counters, licensed music). Use when the owner asks for a new versus/race/challenge reel or types /versus.
---

# /versus - Two Paths "versus" reels, cheap

Read `stick/WORKFLOW.md` (rules) and `stick/HANDOFF.md` (latest notes) first. Answer the owner in Arabic.

## Steps (keep the token cost low)
1. Propose the idea in 5-6 lines: title (question), 2-4 lane labels (archetypes: MOTIVATION / DISCIPLINE /
   OBSESSION...), what each one does, the twist in the last 2 s, the two closing lines. Wait for "نفذ".
2. Copy `stick/versus/mdo.json` to `stick/versus/<name>.json` and edit only the config (no engine code):
   - `dist`: [[t, metres]] keyframes per lane (100 = finish; the counter shows metres * counter_scale).
   - `acts`: [[t, act]] - auto (run/walk from speed), stand, bent, sit, sit_phone, laugh, cheer, sad, grab_head,
     hop, limp, lie. `bubbles`: [[t0, t1, "TEXT"]], `marks`: [[t, "!"]]. `acc`: band | cap | rich | none.
   - `winner`, `lines` (closing two lines, last 2 s), `bars_from` (progress bars), `duration` (18-22 s).
   - `music`: a licensed track in `study/music/` (`fetched.json` lists them; catalog in `catalog.json`):
     `hit_track` = the second of its big hit, `hit_video` = when it must land (the finish / twist).
     Action: "Rynos Theme" (hit 53), "Hitman" (52), "Undaunted", "The Escalation", "Crossing the Chasm".
     Emotional: "Reunited" (swell 38), "Eternal Hope" (244), "Bittersweet", "Sad Trio".
     New tracks: add titles to `study/music_fetch.py` WANT and push (GitHub Actions downloads them).
3. `python3 stick/versus.py stick/versus/<name>.json --stills` -> `stick/versus/<name>-stills.png` (frame 0,
   middle, end). Send ONLY this sheet; fix the config until the owner approves.
4. Full render: `python3 stick/versus.py stick/versus/<name>.json` -> `stick/<name>.mp4` (~2-3 min). It prints the
   music credit line for the description. Commit config + mp4 to `claude/two-paths`, send the mp4 with title,
   first comment, credit line.

## What the data says (keep to it)
- Best performers: a counter + archetype lanes + one clear challenge (Who Wins? race; the reference channel
  @mindframeanim: "Motivation vs Discipline vs Obsession: 365 Days on One Bar" 25.7M, "...: The Mine" 24M).
- Hook in frame 0 (the title question + the counters at 0 + close-ups on the runners); payoff in the last 2 s.
- Post 11 PM - 1 AM Cairo (4-6 PM New York), about one reel a day; titles "A vs B vs C: <challenge>".
