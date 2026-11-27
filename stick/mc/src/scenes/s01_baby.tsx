import {makeScene2D} from '@motion-canvas/2d';
import {all, chain, createRef, easeInCubic, easeOutBack, easeOutCubic, easeOutQuad, waitFor} from '@motion-canvas/core';
import {Stick, STAND} from './stick';
import {stage, FLOOR, T_S, success, shadow} from './stage';
import {countUp, cycle, exact} from './common';

const SIT = {torso: -0.1, legL: 1.45, kneeL: 0.2, legR: 1.25, kneeR: 0.1, armL: 0.6, elbowL: 0.4, armR: -0.4, elbowR: 0.3};
const UPRIGHT = {...STAND, armL: 2.0, elbowL: 0.3, armR: -2.0, elbowR: -0.3};

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.9, y: -280});
  const mom = createRef<Stick>(), kid = createRef<Stick>();
  s.world.add(<Stick ref={mom} mom position={[170, FLOOR - 60]} scaleX={-1} />);
  s.world.add(<Stick ref={kid} head={60} position={[-220, FLOOR - 36]} scale={0.6} />);
  const m = mom(), k = kid();
  m.set({torso: 0.35, legL: -0.2, kneeL: -1.6, legR: 0.6, kneeR: 1.7, armL: 1.6, elbowL: 0.2, armR: 1.3, elbowR: 0.2});
  m.mouth(1);
  k.set(SIT); k.mouth(1);
  const fall = function* (secs: number) {
    k.mouth(0);
    yield* all(k.pose(UPRIGHT, secs * 0.35, easeOutCubic), k.y(FLOOR - 66, secs * 0.35, easeOutCubic));
    yield* all(k.rotation(8, secs * 0.12), k.x(k.x() + 6, secs * 0.12));
    yield* all(k.rotation(-6, secs * 0.12));
    k.mouth(1);
    yield* all(k.pose(SIT, secs * 0.25, easeOutBack), k.y(FLOOR - 36, secs * 0.25, easeOutQuad), k.rotation(0, secs * 0.25));
    yield* waitFor(secs * 0.16);
  };
  yield* exact(all(
    countUp(s.n, 12),
    chain(fall(0.8), fall(0.45), fall(0.35),
      all(success(s, 12), k.pose(UPRIGHT, 0.25), k.y(FLOOR - 66, 0.25)),
      all(k.x(70, 0.55), cycle(k, 0.55, 2.4, 0.35), m.pose({armL: 0.9, armR: 0.7}, 0.55))),
  ));
});
