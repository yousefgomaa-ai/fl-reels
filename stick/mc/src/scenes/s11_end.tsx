import {makeScene2D, Txt} from '@motion-canvas/2d';
import {all, chain, createRef, easeOutCubic, waitFor} from '@motion-canvas/core';
import {Stick} from './stick';
import {stage, FLOOR} from './stage';

export default makeScene2D(function* (view) {
  const s = stage(view, {scale: 1.9, y: -280});
  s.n(100); s.gold(1);
  view.children()[view.children().length - 3].opacity(0);   // hide the TRY header line
  view.children()[view.children().length - 2].opacity(0);
  const mom = createRef<Stick>(), kid = createRef<Stick>();
  s.world.add(<Stick ref={mom} mom position={[120, FLOOR - 60]} scaleX={-1} />);
  s.world.add(<Stick ref={kid} head={60} position={[50, FLOOR - 66]} scale={0.6} />);
  const m = mom(), k = kid();
  m.set({torso: 0.35, legL: -0.2, kneeL: -1.6, legR: 0.6, kneeR: 1.7, armL: 0.9, elbowL: 0.2, armR: 0.7, elbowR: 0.2}); m.mouth(1);
  k.set({armL: 2.0, armR: -2.0}); k.mouth(1);
  const lines = [['YOU NEVER QUIT', '#f6f0e2', -720], ['AS A KID.', '#f6f0e2', -630], ['WHY QUIT NOW?', '#f6c85a', -500]] as const;
  const refs = lines.map(() => createRef<Txt>());
  lines.forEach(([t, c, y], i) => view.add(<Txt ref={refs[i]} y={y} text={t} fontFamily={'Liberation Serif'} fontWeight={700}
                                                 fontSize={i === 2 ? 84 : 70} fill={c} letterSpacing={5} opacity={0} />));
  yield* chain(all(refs[0]().opacity(1, 0.35), refs[1]().opacity(1, 0.5)), waitFor(0.3), refs[2]().opacity(1, 0.35), waitFor(1.0));
});
