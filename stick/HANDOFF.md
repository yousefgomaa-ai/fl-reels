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

## Nov 24 (late) - "Wait For His Last Steps" (stick/steps.py -> steps.mp4, 21.5 s)
- Owner asked for an emotional idea; chose "Wait For His Last Steps". Built on the compare.py night engine (imports it).
- One road of street lamps, AGE counter (1, 6, 16, 25, 40, 45), the father ages (hunch, greyer, a cane); the son
  wears the red scarf. Hook: close-up of a tiny hand around a big finger + HE TAUGHT YOU TO WALK. End mirrors it:
  the old hand holding the son's, HE WAITED FOR YOUR FIRST STEPS. / WAIT FOR HIS LAST ONES.
- Music: emotional piano + strings on FluidSynth, silence when the father's hand is left in the air (AGE 16),
  choir/horn swell when the son comes back.
- steps v2 (owner: no soul, music not dramatic enough): 24.5 s. Colour grade tells the story (warm childhood -> cold blue years -> warm again when he comes back), rain when the son leaves, snow in old age, the rusty little orange bike by the bench (dad touches it), the hand in the air in slow push-in, dad's hand on his heart after the bike, the son stops, drops the briefcase, runs back, kneels, dad's hand on his head; AGE counter rolls through the years. Dramatic score: piano -> strings swells (CC11), heartbeat + low ostinato at 16, silence with one high violin on the hand, timpani/low brass blow, cello lament, sparse piano + clock in the snow, timpani roll on the briefcase, full orchestra + choir at the return.
- steps v3 (owner): two counters YOU / DAD (always 30 apart); DAD's number warms to pale gold after 50 and soft red at 70-75.
- Channel art in the night look (owner): stick/brand_night.py -> stick/avatar/banner-night.png (2560x1440, safe 1546x423 checked) + avatar-night.png (800x800); previews banner-night-phone/desktop.png, avatar-night-circle.png.
- Bolder avatar options (owner keeps the old banner): stick/avatar_pro.py -> avatar-pro-A-fork / B-halo / C-split.png + avatar-pro-compare.png (circle at 400/120/40 px). Recommended B (halo).
- Owner picked option C (split) to develop: avatar-pro-C2-split.png (rain on the cold side, light rays and sparks on the warm side, coloured rim glows, wet-floor reflections, a glowing seam, two-tailed scarf, vignette) + avatar-pro-C2-preview.png.
- Facebook page art: stick/fb_cover.py -> stick/avatar/fb-cover.png (1640x924; desktop band 1640x624 and phone view with the profile circle checked: fb-cover-desktop.png, fb-cover-phone.png); profile = avatar-pro-C2-split.png.

## Nov 25 - "Would You Press It?" (stick/button.py -> button.mp4, 20 s)
- Owner wanted a strong hook. Frame 0: a big red button under a spotlight, a glowing $1,000,000 sign, header
  WOULD YOU PRESS IT?. Split screen (top PRESSES = red-scarf hero, bottom READS FIRST), night-stage engine
  (compare.py) rendered per panel and cropped to a band. Each press: money rains, the pile grows ($1M -> $6M) and he
  ages 10 years (25 -> 85, hunch, grey, cane, colder grade). The reader reads the plate, shakes his head, walks to a
  warm table with two friends. 15.8 s: the camera dives into the plate - EACH PRESS = 10 YEARS OF YOUR LIFE; the old
  man reaches for the button again. YOU CAN EARN MONEY BACK. / NOT TIME. Music: accelerating ostinato + taiko and
  a brass/timpani hit on every press, then a sad piano/cello turn, a low hit on the reveal, a held chord at the end.

## Nov 25 - licensed music + "The Hourglass" (stick/hourglass.py -> hourglass.mp4, 22 s)
- Owner: the FluidSynth music sounds cheap/no soul -> use ready licensed music. GitHub Actions fetch it
  (music-catalog.yml: incompetech catalog JSON with feel/bpm/instruments, 1443 tracks; music-fetch.yml: chosen mp3s
  into study/music/). Tracks: Eternal Hope, Reunited, Bittersweet, Sad Trio, Touching Moments Four, Immersed.
  Licence CC BY 4.0: put the credit line in the description, e.g.
  Music: "Reunited" by Kevin MacLeod (incompetech.com), CC BY 4.0
- The Hourglass: everyone has a glowing hourglass above the head (hook: WHAT IF YOU COULD SEE EVERYONE'S TIME?);
  old man feeding pigeons (almost empty, smiling), man shouting at a waiter (half), home: mom at the table, her hand
  rises and falls as he passes with headphones; at his door he stops, turns; the camera dives into her hourglass
  (music ducked, heartbeat); headphones drop, he runs back and holds her; the last grain hangs. Reunited is cut from
  22 s so its swell lands on the hug. YOU CAN'T SEE IT. / BUT IT'S RUNNING.

## Nov 25 - "The Rope" (stick/rope.py -> rope.mp4, 20 s)
- Owner rejected the hourglass (who is mom/dad unclear, no pull at the start) and asked for strong-hook ideas; chose
  The Rope. Frame 0: close-up of a rope fraying over a rock lip + THE ROPE CAN ONLY HOLD ONE., ROPE % counter
  (62 -> 0). Hero (red scarf) above, stranger (yellow helmet, backpack) below; the stranger points at the hero's
  knife; trembling hesitation; the knife thrown into the dark; he grabs the stranger, they climb (snaps, a slip),
  he hauls him over the edge as the rope snaps. HE COULD HAVE CUT IT. / HE CHOSE NOT TO.
- Music: "Immersed" (tension) then "Eternal Hope" from 228 s so its swell (244 s) lands on the rescue - both Kevin
  MacLeod, CC BY 4.0 (credit both in the description).
- rope v2 (owner: not gripping - add more consequences while they hang): a rock knocked loose hits the stranger's helmet (crack, sparks), the anchor creaks out of the rock (cutaway), lightning + rain, the stranger's other hand slips (he hangs only from the hero's hand), a gust slams them into the wall, the edge crumbles under the hero's hand, the anchor rips free with the last strand; ROPE drops in jumps on each event; 21 s. The two hang side by side (no overlap).
- rope v3 (owner: the music was very bad, wanted energetic music that fits): five licensed action tracks fetched (The Escalation, Undaunted, Crossing the Chasm, Rynos Theme, Hitman); The Rope now uses "Rynos Theme" (Kevin MacLeod, CC BY 4.0) from 36 s - driving from frame 0, its dip at 52 s and big hit at 53 s land on the snap.
