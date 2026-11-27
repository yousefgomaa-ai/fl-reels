import {Circle, Line, makeScene2D, Node} from '@motion-canvas/2d';
import {all, chain, createRef, createSignal, easeInCubic, easeOutBack, linear, waitFor, Vector2} from '@motion-canvas/core';
import {Stick} from './stick';
import {stage, FLOOR, success} from './stage';
import {countUp, exact} from './common';

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.7, y: -300});
  const rig = createRef<Node>();
  const ped = createSignal(0);
  s.world.add(<Node ref={rig} position={[-330, FLOOR]}>
    <Circle position={[-70, -36]} size={72} stroke={'#b4b8c4'} lineWidth={6} />
    <Circle position={[70, -36]} size={72} stroke={'#b4b8c4'} lineWidth={6} />
    <Line points={[[-70, -36], [-10, -36], [30, -90], [70, -36]]} stroke={'#3c8cdc'} lineWidth={7} lineCap={'round'} />
    <Line points={[[-10, -36], [-30, -96]]} stroke={'#3c8cdc'} lineWidth={7} lineCap={'round'} />
    <Line points={[[30, -90], [42, -124]]} stroke={'#5a5c66'} lineWidth={6} lineCap={'round'} />
    <Stick scarf position={[-24, -98]} />
  </Node>);
  const r = rig();
  const h = r.children()[5] as Stick;
  h.set({torso: 0.35, armL: 1.25, elbowL: 0.2, armR: 1.1, elbowR: 0.2});
  h.legL(() => 0.9 + 0.5 * Math.sin(ped()));
  h.kneeL(() => 1.1 + 0.5 * Math.cos(ped()));
  h.legR(() => 0.9 - 0.5 * Math.sin(ped()));
  h.kneeR(() => 1.1 - 0.5 * Math.cos(ped()));
  const tryOnce = function* (secs: number) {
    r.position([-330, FLOOR]); r.rotation(0); h.mouth(0);
    yield* all(r.x(-180, secs, linear), ped(ped() + 8, secs, linear),
      chain(waitFor(secs * 0.35), r.rotation(-12, secs * 0.2), r.rotation(16, secs * 0.15), r.rotation(80, secs * 0.3, easeInCubic)));
    h.mouth(-1);
  };
  yield* exact(all(
    countUp(s.n, 7),
    chain(tryOnce(0.75), tryOnce(0.45), tryOnce(0.4),
      all(success(s, 7), (function* () { r.position([-330, FLOOR]); r.rotation(0); h.mouth(1);
        yield* all(r.x(330, 0.8, linear), ped(ped() + 14, 0.8, linear), chain(waitFor(0.3), h.pose({armR: -2.6, elbowR: -0.2}, 0.25, easeOutBack))); })())),
  ));
});
