import {makeScene2D} from '@motion-canvas/2d';
import {all, chain, createRef, easeInCubic, easeInOutCubic, easeOutBack, easeOutCubic, easeOutQuad, waitFor} from '@motion-canvas/core';
import {Stick, STAND} from './stick';
import {stage, FLOOR, success} from './stage';
import {countUp, exact} from './common';

const TUCK = {torso: 0.2, legL: 2.0, kneeL: 2.3, legR: 1.9, kneeR: 2.2, armL: 1.2, elbowL: 0.6, armR: 1.0, elbowR: 0.6};
const CROUCH = {torso: 0.3, legL: 0.9, kneeL: 1.6, legR: 0.8, kneeR: 1.5, armL: -0.9, elbowL: 0.2, armR: -1.1, elbowR: 0.2};
const LYING = {torso: 0, legL: 0.12, kneeL: 0.3, legR: -0.12, kneeR: 0.2, armL: 1.0, elbowL: 0.2, armR: -1.2, elbowR: 0.2};

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.8, y: -230});
  const r = createRef<Stick>();
  s.world.add(<Stick ref={r} scarf position={[0, FLOOR - 113]} />);
  const h = r();
  const flip = function* (ok: boolean, secs: number) {
    h.position([0, FLOOR - 113]); h.rotation(0); h.set(STAND); h.mouth(0);
    yield* all(h.pose(CROUCH, secs * 0.2, easeOutQuad), h.y(FLOOR - 80, secs * 0.2));
    yield* all(h.pose(TUCK, secs * 0.2), h.y(FLOOR - 360, secs * 0.4, easeOutCubic), h.x(-40, secs * 0.6),
      h.rotation(ok ? -360 : -250, secs * 0.6, easeInOutCubic),
      chain(waitFor(secs * 0.4), h.y(ok ? FLOOR - 113 : FLOOR - 26, secs * 0.2, easeInCubic)),
      chain(waitFor(secs * 0.35), h.pose(ok ? STAND : LYING, secs * 0.25)));
    if (!ok) { h.mouth(-1); yield* all(h.rotation(-270, secs * 0.15, easeOutBack)); }
  };
  yield* exact(all(
    countUp(s.n, 40),
    chain(flip(false, 0.8), flip(false, 0.4), flip(false, 0.4),
      all(success(s, 40), chain(flip(true, 0.55), (function* () { h.mouth(1); yield* h.pose({armL: 2.7, armR: -2.7, elbowL: 0.1, elbowR: -0.1}, 0.2, easeOutBack); })()))),
  ));
});
