# Handoff (Nov 24, 2026) - read this, then WORKFLOW.md (rules 1-17), then IDEAS.md

**Owner writes in Arabic; answer in Arabic.** Channel: "Two Paths" stickman Shorts, Western audience.
Push only to branch `claude/two-paths` of yousefgomaa-ai/fl-reels; never main; no PRs.
Every reel: propose first, build after "نفذ"; send it with idea, title, first comment, and the viewer review
(why swipe / keep watching / watch to the end / rewatch reason, honest scores). Fix before sending (rule 6).

## Where we are
- Best reel so far: "The Only Difference Was One More Try" (gap_split.py): 54.5% stayed. Template = rule 15.
- Channel data and lessons: WORKFLOW.md rules 13-17 (STICK TO IT study: they build with Claude Code too).
- New engine in progress: **Blender (3D white figures, spotlights) + FluidSynth (real instruments)**.
  - `stick/dishes_bl.py` renders one panel ("later" / "now") as PNGs with Cycles (~4 s/frame, 510 frames each).
  - `stick/dishes.py` lays out both panels + "WILL IT FALL?", labels, DAY counter, closing lines, music, SFX.
  - Status: the full render was running when the session ended - **re-render and assemble**:
    ```
    apt-get install -y fluidsynth fluid-soundfont-gm libegl1 && apt-get install -y --no-install-recommends blender
    pip install mido pymunk skia-python
    blender -b --python stick/dishes_bl.py -- later /tmp/dl/later all
    blender -b --python stick/dishes_bl.py -- now /tmp/dl/now all
    python3 stick/dishes.py /tmp/dl stick/dishes.mp4
    ```
  - Then review frames (frame 0 vs last frame must match), send to the owner with the review.
- Owner's posting advice given: one reel a day, 6:15 PM Cairo (11:15 AM New York), video language English,
  don't share links with Egyptian friends in the first 24 h.
