import {Line, makeScene2D, Node, Rect} from '@motion-canvas/2d';
import {all, chain, createRef, createSignal, easeInCubic, easeOutBack, easeOutQuad, waitFor} from '@motion-canvas/core';
import {Stick, STAND} from './stick';
import {stage, FLOOR, success} from './stage';
import {countUp, exact} from './common';

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.65, y: -170});
  const lift = createSignal(0);        // 0 floor .. 0.5 hips .. 1 overhead
  const shake = createSignal(0);
  const r = createRef<Stick>();
  s.world.add(<Stick ref={r} scarf position={[0, FLOOR - 113]} />);
  const h = r();
  const barY = () => FLOOR - 50 - 420 * lift();
  h.y(() => FLOOR - 113 + 45 * Math.max(0, 1 - lift() * 2.5));
  h.torso(() => 0.6 * Math.max(0, 1 - lift() * 2.5));
  h.legL(() => 0.9 * Math.max(0, 1 - lift() * 2.5) + 0.12); h.kneeL(() => 1.6 * Math.max(0, 1 - lift() * 2.5));
  h.legR(() => 0.8 * Math.max(0, 1 - lift() * 2.5) - 0.12); h.kneeR(() => 1.5 * Math.max(0, 1 - lift() * 2.5));
  h.armL(() => lift() < 0.55 ? 0.3 : 0.3 + (lift() - 0.55) / 0.45 * 2.7); h.elbowL(0.05);
  h.armR(() => lift() < 0.55 ? -0.3 : -0.3 - (lift() - 0.55) / 0.45 * 2.7); h.elbowR(-0.05);
  s.world.add(<Node position={() => [0, barY()]} rotation={() => 4 * Math.sin(shake() * 40) * shake()}>
    <Line points={[[-190, 0], [190, 0]]} stroke={'#c0c4ce'} lineWidth={8} lineCap={'round'} />
    {[-170, -148, 148, 170].map((x) => <Rect x={x} size={[16, 96]} radius={3} fill={'#2a2c34'} stroke={'#70748a'} lineWidth={2} />)}
  </Node>);
  const fail = function* (secs: number) {
    h.mouth(-1); h.eyes(0.4);
    yield* all(lift(0.45, secs * 0.45, easeOutQuad), shake(1, secs * 0.45));
    yield* all(lift(0, secs * 0.3, easeInCubic), shake(0, secs * 0.3));
    yield* waitFor(secs * 0.25);
  };
  yield* exact(all(
    countUp(s.n, 90),
    chain(fail(0.7), fail(0.45), fail(0.45),
      all(success(s, 90), (function* () { h.mouth(0); yield* all(lift(1, 0.45, easeOutBack), shake(0.6, 0.45)); h.mouth(1); h.eyes(1); yield* shake(0, 0.3); })())),
  ));
});
