import {Line, makeScene2D, Rect} from '@motion-canvas/2d';
import {all, chain, createRef, easeInCubic, easeInOutCubic, easeInOutSine, easeOutBack, easeOutQuad, linear, waitFor} from '@motion-canvas/core';
import {Stick, STAND} from './stick';
import {stage, FLOOR, success} from './stage';
import {countUp, cycle, exact} from './common';

const BAR_X = 120, BAR_Y = FLOOR - 230;

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.6, x: -80, y: -250});
  s.world.add(<Rect position={[BAR_X + 150, FLOOR - 36]} size={[260, 72]} radius={10} fill={'#2d4fae'} />);
  for (const dx of [-14, 70]) s.world.add(<Rect position={[BAR_X + dx, FLOOR - 135]} size={[8, 270]} fill={'#d6d6de'} />);
  const bar = createRef<Line>();
  s.world.add(<Line ref={bar} points={[[BAR_X - 14, 0], [BAR_X + 70, 0]]} y={BAR_Y} stroke={'#f0d23c'} lineWidth={7} lineCap={'round'} />);
  const r = createRef<Stick>();
  s.world.add(<Stick ref={r} scarf position={[-420, FLOOR - 113]} />);
  const h = r();
  const attempt = function* (ok: boolean, secs: number) {
    h.position([-420, FLOOR - 113]); h.set(STAND); h.torso(0.25); bar().rotation(0); bar().y(BAR_Y); bar().x(0); h.mouth(0);
    yield* all(h.x(BAR_X - 120, secs * 0.45, easeInOutSine), cycle(h, secs * 0.45, 2.6, 0.8));
    const up = ok ? 300 : 245;
    yield* all(
      h.x(BAR_X + 120, secs * 0.45, linear),
      chain(h.y(FLOOR - 113 - up, secs * 0.22, easeOutQuad), h.y(FLOOR - 120, secs * 0.23, easeInCubic)),
      h.torso(-1.55, secs * 0.32, easeInOutCubic),
      h.pose({legL: 1.2, legR: 1.0, kneeL: 1.4, kneeR: 1.2, armL: 2.4, armR: 2.6, elbowL: 0.2, elbowR: 0.2}, secs * 0.3),
      ok ? waitFor(0) : chain(waitFor(secs * 0.2), all(bar().rotation(28, secs * 0.25, easeInCubic), bar().y(FLOOR - 60, secs * 0.25, easeInCubic), bar().x(30, secs * 0.25))),
    );
    if (!ok) { h.mouth(-1); yield* waitFor(secs * 0.1); }
  };
  yield* exact(all(
    countUp(s.n, 100),
    chain(attempt(false, 0.8), attempt(false, 0.4), attempt(false, 0.4),
      all(success(s, 100), s.sky(1, 0.7), chain(attempt(true, 0.55), (function* () { h.mouth(1);
        yield* all(h.y(FLOOR - 113, 0.2), h.pose({torso: 0, legL: 0.12, legR: -0.12, kneeL: 0, kneeR: 0, armL: 2.7, armR: -2.7, elbowL: 0.1, elbowR: -0.1}, 0.2, easeOutBack)); })()))),
  ));
});
