import {Circle, Line, makeScene2D, Rect} from '@motion-canvas/2d';
import {all, chain, createRef, createSignal, easeInCubic, easeInOutSine, easeOutBack, linear, waitFor} from '@motion-canvas/core';
import {Stick} from './stick';
import {stage, FLOOR, success} from './stage';
import {countUp, exact} from './common';

const TOP = FLOOR - 640;

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.35, y: 0});
  s.world.add(<Rect position={[40, (TOP + FLOOR) / 2]} size={[300, FLOOR - TOP]} fill={'#2a2d3a'} stroke={'#4a4e60'} lineWidth={4} />);
  const cols = ['#e05a3c', '#3cb4e0', '#f0c83c', '#6cd070'];
  for (let i = 0; i < 18; i++) {
    s.world.add(<Circle position={[40 + ((i * 67) % 220) - 110, FLOOR - 40 - i * 33]} size={18} fill={cols[i % 4]} />);
  }
  s.world.add(<Rect position={[40, FLOOR - 18]} size={[360, 36]} radius={8} fill={'#2d4fae'} />);
  const bell = createSignal(0);
  s.world.add(<Circle position={[40, TOP - 10]} size={46} fill={'#f0c83c'} rotation={() => 20 * Math.sin(bell() * 30) * (1 - bell())} />);
  const r = createRef<Stick>();
  s.world.add(<Stick ref={r} scarf position={[20, FLOOR - 150]} />);
  const h = r();
  const ph = createSignal(0);
  const climbPose = () => {
    h.armL(() => Math.PI - 0.3 + 0.35 * Math.sin(ph())); h.elbowL(() => 0.3 + 0.3 * Math.cos(ph()));
    h.armR(() => -(Math.PI - 0.3) + 0.35 * Math.sin(ph())); h.elbowR(() => -0.3 - 0.3 * Math.cos(ph()));
    h.legL(() => 0.4 + 0.4 * Math.sin(ph())); h.kneeL(() => 0.9 - 0.4 * Math.sin(ph()));
    h.legR(() => -0.1 - 0.4 * Math.sin(ph())); h.kneeR(() => 0.9 + 0.4 * Math.sin(ph()));
  };
  const attempt = function* (height: number, secs: number) {
    h.position([20, FLOOR - 150]); h.rotation(0); h.mouth(0); climbPose();
    yield* all(h.y(FLOOR - 150 - height, secs * 0.65, easeInOutSine), ph(ph() + 7, secs * 0.65, linear));
    h.mouth(-1);
    yield* all(h.y(FLOOR - 60, secs * 0.25, easeInCubic), h.rotation(-25, secs * 0.25), h.pose({armL: 2.4, armR: -2.4}, secs * 0.2));
    yield* waitFor(secs * 0.1);
  };
  yield* exact(all(
    countUp(s.n, 25),
    chain(attempt(220, 0.7), attempt(330, 0.45), attempt(420, 0.45),
      all(success(s, 25), (function* () {
        h.position([20, FLOOR - 150]); h.rotation(0); h.mouth(1); climbPose();
        yield* all(h.y(TOP + 130, 0.55, easeInOutSine), ph(ph() + 9, 0.55, linear));
        h.set({armR: -2.9, elbowR: -0.1});
        yield* bell(1, 0.25);
      })())),
  ));
});
