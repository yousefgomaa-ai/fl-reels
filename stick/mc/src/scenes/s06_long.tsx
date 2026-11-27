import {Circle, makeScene2D, Rect, Txt} from '@motion-canvas/2d';
import {all, chain, createRef, createSignal, easeInCubic, easeOutBack, easeOutQuad, waitFor} from '@motion-canvas/core';
import {Stick} from './stick';
import {stage, FLOOR, success} from './stage';
import {countUp, cycle, exact} from './common';

const LAND = {torso: 0.5, legL: 1.5, kneeL: 1.6, legR: 1.4, kneeR: 1.5, armL: 1.6, elbowL: 0.3, armR: 1.4, elbowR: 0.3};
const AIR = {torso: -0.1, legL: 1.3, kneeL: 0.4, legR: 1.1, kneeR: 0.6, armL: 2.6, elbowL: 0.2, armR: 2.4, elbowR: 0.2};
const FACE = {torso: 1.4, legL: -0.2, kneeL: 0.1, legR: 0.1, kneeR: 0.1, armL: 2.0, elbowL: 0.2, armR: 1.8, elbowR: 0.2};

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.3, x: -230, y: -150});
  s.world.add(<Rect position={[250, FLOOR + 10]} size={[460, 26]} fill={'#c8a868'} radius={6} />);
  s.world.add(<Rect position={[10, FLOOR + 6]} size={[18, 12]} fill={'#eeeeee'} />);
  const mark = createSignal(0);
  s.world.add(<Rect position={[440, FLOOR - 40]} size={[6, 80]} fill={'#f0c83c'} />);
  s.world.add(<Txt position={[440, FLOOR - 100]} text={'RECORD'} fontFamily={'Inter'} fontWeight={800} fontSize={26} fill={'#f0c83c'} />);
  const r = createRef<Stick>();
  s.world.add(<Stick ref={r} scarf position={[-420, FLOOR - 113]} />);
  const h = r();
  const jump = function* (dist: number, ok: boolean, secs: number) {
    h.position([-420, FLOOR - 113]); h.rotation(0); h.mouth(0); h.torso(0.25);
    yield* all(h.x(0, secs * 0.45), cycle(h, secs * 0.45, 2.8, 0.8));
    yield* all(h.pose(AIR, secs * 0.15),
      h.x(dist, secs * 0.4),
      chain(h.y(FLOOR - 113 - 150, secs * 0.2, easeOutQuad), h.y(FLOOR - 70, secs * 0.2, easeInCubic)));
    if (ok) { yield* h.pose(LAND, 0.1, easeOutBack); }
    else { h.mouth(-1); yield* all(h.pose(FACE, secs * 0.15), h.y(FLOOR - 20, secs * 0.15)); }
  };
  yield* exact(all(
    countUp(s.n, 50),
    chain(jump(140, false, 0.75), jump(220, false, 0.42), jump(300, false, 0.42),
      all(success(s, 50), chain(jump(470, true, 0.6), (function* () { h.mouth(1);
        yield* all(h.y(FLOOR - 113, 0.2), h.pose({torso: 0, legL: 0.12, kneeL: 0, legR: -0.12, kneeR: 0, armL: 2.7, armR: -2.7}, 0.2, easeOutBack)); })()))),
  ));
});
