import {makeScene2D, Rect} from '@motion-canvas/2d';
import {all, chain, createRef, createSignal, easeInOutSine, easeOutBack, waitFor} from '@motion-canvas/core';
import {Stick} from './stick';
import {stage, FLOOR, success} from './stage';
import {countUp, exact} from './common';

const BAR = FLOOR - 470;

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.6, y: 40});
  for (const x of [-170, 170]) s.world.add(<Rect position={[x, (BAR + FLOOR) / 2]} size={[12, FLOOR - BAR]} fill={'#5a5c66'} />);
  s.world.add(<Rect position={[0, BAR]} size={[360, 10]} radius={5} fill={'#a8aab4'} />);
  const r = createRef<Stick>();
  s.world.add(<Stick ref={r} scarf position={[0, BAR + 190]} />);
  const h = r();
  const up = createSignal(0);
  // the arms always reach the bar: solve the elbow from the hip height
  h.y(() => BAR + 190 - 120 * up());
  h.armL(() => Math.PI - 0.35 + 0.9 * up()); h.elbowL(() => -0.1 - 2.0 * up());
  h.armR(() => -(Math.PI - 0.35) - 0.9 * up()); h.elbowR(() => 0.1 + 2.0 * up());
  h.set({legL: 0.1, kneeL: 0.4, legR: 0.0, kneeR: 0.5});
  const strain = function* (secs: number) {
    h.mouth(-1); h.eyes(0.3);
    yield* chain(up(0.25, secs * 0.4, easeInOutSine), up(0.2, secs * 0.2), up(0.28, secs * 0.2), up(0, secs * 0.2));
  };
  yield* exact(all(
    countUp(s.n, 30),
    chain(strain(0.7), strain(0.45), strain(0.45),
      all(success(s, 30), (function* () { h.mouth(1); h.eyes(1);
        yield* chain(up(1, 0.35, easeOutBack), up(0.1, 0.3), up(1, 0.3, easeOutBack)); })())),
  ));
});
