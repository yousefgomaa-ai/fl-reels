import {Circle, Line, makeScene2D, Node} from '@motion-canvas/2d';
import {all, chain, createRef, createSignal, easeInCubic, easeOutBack, easeOutQuad, linear, waitFor, Vector2} from '@motion-canvas/core';
import {Stick} from './stick';
import {stage, FLOOR, success} from './stage';
import {countUp, exact} from './common';

const GX = 330, GH = 260;

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.35, x: 10, y: -120});
  const bulge = createSignal(0);
  s.world.add(<Line points={[[GX, FLOOR], [GX, FLOOR - GH], [GX + 170, FLOOR - GH + 30], [GX + 170, FLOOR]]} stroke={'#f0f0f5'} lineWidth={9} lineCap={'round'} />);
  for (let j = 0; j < 8; j++) {
    s.world.add(<Line points={() => [[GX + 4, FLOOR - GH + 10 + j * 32], [GX + 160 + 40 * bulge() * Math.sin(j), FLOOR - GH + 26 + j * 30]]}
                      stroke={'#dcdce2'} lineWidth={2} opacity={0.6} />);
  }
  const kr = createRef<Stick>(), hr = createRef<Stick>(), ball = createRef<Circle>();
  s.world.add(<Stick ref={kr} position={[GX - 50, FLOOR - 113]} scaleX={-1} shirt={'#3ca050'} />);
  s.world.add(<Stick ref={hr} scarf position={[-330, FLOOR - 113]} />);
  s.world.add(<Circle ref={ball} position={[-250, FLOOR - 22]} size={44} fill={'#f2f2f2'} stroke={'#222'} lineWidth={3} />);
  const k = kr(), h = hr(), b = ball();
  k.set({armL: 0.9, armR: -0.9});
  const shot = function* (target: [number, number], kind: string, secs: number) {
    b.position([-250, FLOOR - 22]); k.rotation(0); k.position([GX - 50, FLOOR - 113]); h.mouth(0); k.mouth(0);
    yield* h.pose({legR: -0.9, kneeR: 1.2, armL: 0.9}, secs * 0.25);
    yield* all(h.pose({legR: 1.3, kneeR: 0.1}, secs * 0.12, easeOutQuad),
      b.position(new Vector2(target[0], target[1]), secs * 0.35, linear),
      kind === 'save' || kind === 'goal' ? all(k.rotation(-55, secs * 0.35), k.y(FLOOR - 170, secs * 0.35)) : waitFor(0));
    if (kind === 'post') yield* b.position([GX - 160, FLOOR - 22], secs * 0.3, easeInCubic);
    if (kind === 'wide') yield* b.position([GX + 260, FLOOR - 400], secs * 0.2);
    h.set({legR: -0.12, kneeR: 0}); h.mouth(kind === 'goal' ? 1 : -1);
  };
  yield* exact(all(
    countUp(s.n, 70),
    chain(shot([GX, FLOOR - GH], 'post', 0.75), shot([GX + 120, FLOOR - 420], 'wide', 0.42), shot([GX - 80, FLOOR - 150], 'save', 0.43),
      all(success(s, 70), chain(shot([GX + 30, FLOOR - GH + 26], 'goal', 0.5), all(bulge(1, 0.15), h.pose({armL: 2.7, armR: -2.7}, 0.2, easeOutBack)), bulge(0, 0.3)))),
  ));
});
