# Handoff (Nov 24, 2026) - read this, then WORKFLOW.md (rules 1-17), then IDEAS.md

**Owner writes in Arabic; answer in Arabic.** Channel: "Two Paths" stickman Shorts, Western audience.
Push only to branch `claude/two-paths` of yousefgomaa-ai/fl-reels; never main; no PRs.
Every reel: propose first, build after "نفذ"; send it with idea, title, first comment, and the viewer review
(why swipe / keep watching / watch to the end / rewatch reason, honest scores). Fix before sending (rule 6).

## Where we are
- Best reel so far: "The Only Difference Was One More Try" (gap_split.py): 54.5% stayed. Template = rule 15.
- Channel data and lessons: WORKFLOW.md rules 13-17 (STICK TO IT study: they build with Claude Code too).
- **Owner's decision (Nov 24): the new session keeps the OLD system** - the Python/PIL engine (`stick/hq.py`,
  split-screen reels like `gap_split.py`, `couch.py`, `fishing.py`) with synthesized sound (`stick/music.py`).
  Do not switch to Blender unless the owner asks.
- Experimental, parked: a Blender + FluidSynth engine (`stick/dishes_bl.py`, `stick/dishes.py`, the "WILL IT FALL?"
  dishes reel). Only if the owner asks for it again.
- Next step: propose the next reel from IDEAS.md (Tier A) following rules 11-16 (split screen, one big visible
  goal or one escalating thing, big thick white figures, one counter, answer held to the end, no tail, 15-18 s,
  perfect loop), wait for "نفذ", build, review, send.
- Owner's posting advice given: one reel a day, 6:15 PM Cairo (11:15 AM New York), video language English,
  don't share links with Egyptian friends in the first 24 h.

## Nov 24 (later)
- Built `stick/race.py` -> `who-wins.mp4`: the owner's own idea - three lanes (SPRINTER straight road / CONSISTENT
  winding road / RICH KID with a gift car), 26.8 s (owner asked for 26 s+), night look copied from the perfect_wave
  reference (navy sky, stars, moon halo, light-grey glowing figures, spaced Inter type), one counter on top:
  DISTANCE (M) for all three; the rich kid sits at 0 until the last second. Loop = a fast rewind into frame 0.
  Music strings_am. Waiting for the owner's numbers.
- Owner's notes on v1 (applied, v2): no finish line in frame 0 - each lane has its own camera following its runner,
  the finish only appears at the end; smaller figures in proportion to the road (S=0.62, 1 m = 100 px, real-size
  car); realistic run cycle (knee fold, bent arms, lean, feet grounded, cadence from speed: sprinter 9 m/s, consistent
  3.8 m/s jog); the rich kid starts on a lounger with no car, the car arrives with a chauffeur before the end; the
  sprinter rests (water, leans back, phone) instead of sleeping. 29.6 s; 25/50/75 M signs on the roads.
- v3 (owner): energetic synthesized race track (140 BPM, drums/bass/arps, build into the launch) instead of strings_am; no TIRED/2ND/1ST stamps - the gold 100 on the counter tells the result; 28.8 s.
- v4 (owner): music = an epic hybrid cue on real GM instruments via FluidSynth (race.gm_score; needs `apt-get install -y fluidsynth fluid-soundfont-gm` and `pip install mido`); the gift bow no longer flies off the car at launch.
- v5 (owner): opening close-up on all three (camera starts ~1.85x on each figure, pulls back by ~1.9 s), both runners caught mid-stride at frame 0, counter with one decimal (moves every frame), payoff 1.7 s before the end (DUR 27.95, rewind from 27.15).
- v6 (owner: shorter): 23.85 s - CONSISTENT jogs 4.5 m/s, the sprinter's rest is 6.2 s, the rich kid's beats compressed; car crosses at 22.15, CONSISTENT at 22.52, rewind 23.05.
- v7 (owner): mid-video re-hook 9.5-12.0 s - a progress bar at the top of each panel with the metres left (rich kid: 100.0 M LEFT in red) + a pop sound.
- v8 (owner): 21.6 s (CONSISTENT 5 m/s, rest 5 s); the metres-left bars appear at 8 s and stay to the end.
- v9 (owner): the metres-left bars now appear at 6 s.
- v10 (owner): the metres-left bars sit at the bottom of each panel (slimmer), from 4 s to the end; the lounger moved up onto the road so the bar doesn't hide the rich kid.

## Nov 24 (night) - "When You Compare Yourself" (stick/compare.py -> compare.mp4)
- Owner sent a Simply Animated Short ("When Your Ego Gets Hurt", 16K likes; study/links/vpC4AnQJ4Yo - YouTube blocked
  the download, only the thumbnail + 3 preview frames). Format: a montage of short night scenes, one small serif line
  each. Owner wanted the same professional night look and an energetic cinematic sound (not their track).
- New engine in compare.py: stage_bg (black stage + spotlight cones + floor pool + vignette), volumetric figures
  (figure(): lit edge / far-side shadow / dark outline from the silhouette mask), wet-floor reflection, depth of field,
  dust in the light, spaced serif captions; music on FluidSynth (piano ostinato, cellos, taiko, strings, brass/choir
  at the flip, hits on every cut). 19.3 s, 5 scenes + flip; the barefoot observer is hidden blurred in scene 1.
- v2 (owner: more motion, clearer situations, the phone idea is unclear): 20.3 s - S0 'the grass is greener' (his lawn dries as he looks over the fence), S1 tracking bike + the car passes and splashes him, S2 the barbell slammed down (shake), S3 payday envelopes (the colleague's bursts with money, a whip pan), S4 he runs through a 5K FINISH arch, the giant screen shows a marathon winner, S5 the reveal; moving cameras, whip-ins on every cut.
- v3 (owner: the grass looked bad, didn't like the ending; chose ending B): lawns are now raised turf patches (lit edge, tufts, flowers, bush), both gardens in view from frame 0, the neighbour's lusher; a dark figure peeks over the left fence at HIS garden (hidden detail). New ending: the camera pulls back over a row of gardens, everyone leaning on a fence staring at the next one, lights come on one by one: EVERYONE IS LOOKING / AT SOMEONE ELSE'S GRASS. 21.5 s.
- v4 (owner chose hook 1): frame 0 = he leans on the fence staring at the lush garden while his own lawn is already yellowing and crackles dry; big serif question WHY IS HIS GRASS / DYING? for 1.5 s, then the small WHEN YOU COMPARE YOURSELF.
