import {Line, makeScene2D} from '@motion-canvas/2d';
import {all, chain, createRef, createSignal, easeOutCubic, linear, waitFor, Vector2} from '@motion-canvas/core';
import {Stick} from './stick';
import {stage, FLOOR, success} from './stage';
import {countUp, exact} from './common';

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.9, y: -260});
  const hr = createRef<Stick>();
  s.world.add(<Stick ref={hr} scarf position={[0, FLOOR - 113]} />);
  const h = hr();
  const a = createSignal(0);           // rope angle
  const caught = createSignal(0);
  h.set({armL: 0.6, elbowL: -0.9, armR: -0.6, elbowR: 0.9});
  h.y(() => FLOOR - 113 - (1 - caught()) * 58 * Math.max(0, -Math.cos(a())) ** 3);
  h.kneeL(() => 0.5 * Math.max(0, -Math.cos(a())) ** 3); h.kneeR(() => 0.5 * Math.max(0, -Math.cos(a())) ** 3);
  const hand = (side: number) => h.position().add(new Vector2(side * 52, -60));
  s.world.add(<Line points={() => {
    const l = hand(-1), r = hand(1);
    const mid = caught() > 0.5 ? new Vector2(0, FLOOR - 6) :
      new Vector2(40 * Math.sin(a()), (h.y() - 210) + (FLOOR + 6 - (h.y() - 210)) * (1 - Math.cos(a())) / 2);
    const ctrl = mid.scale(2).sub(l.add(r).scale(0.5));
    const pts: Vector2[] = [];
    for (let i = 0; i <= 16; i++) {
      const t = i / 16;
      pts.push(l.scale((1 - t) ** 2).add(ctrl.scale(2 * (1 - t) * t)).add(r.scale(t * t)));
    }
    return pts;
  }} stroke={'#f0c83c'} lineWidth={5} lineCap={'round'} />);
  const miss = function* (secs: number) {
    caught(0); h.mouth(0); h.torso(0);
    yield* a(a() + Math.PI * 1.6, secs * 0.6, linear);
    caught(1); h.mouth(-1);
    yield* all(h.torso(0.35, secs * 0.2), h.pose({legR: -0.5, kneeR: 0.6}, secs * 0.2));
    yield* all(h.torso(0, secs * 0.2), h.pose({legR: -0.12, kneeR: 0}, secs * 0.2));
    a(Math.PI * 2 * Math.ceil(a() / (Math.PI * 2)));
  };
  yield* exact(all(
    countUp(s.n, 15),
    chain(miss(0.7), miss(0.45), miss(0.45),
      all(success(s, 15), (function* () { caught(0); h.mouth(1); yield* a(a() + Math.PI * 2 * 3.2, 0.8, linear); })())),
  ));
});
