import {Circle, Line, makeScene2D, Node, Rect, Txt, Polygon} from '@motion-canvas/2d';
import {all, chain, createRef, createSignal, easeInCubic, easeInOutCubic, easeInOutSine, easeOutBack, easeOutCubic,
  easeOutQuad, linear, loop, sequence, waitFor, Color, Vector2} from '@motion-canvas/core';
import {Stick} from './stick';

const FLOOR = 300;           // ground line (scene coords, centre = 0)
const BAR_X = 120, BAR_Y = FLOOR - 230;

export default makeScene2D(function* (view) {
  const sky = createSignal(0);    // 0 night .. 1 sunrise
  view.add(<Rect size={[1080, 1920]} fill={() => Color.lerp('#090b13', '#3a2e5c', sky())} />);
  const world = createRef<Node>();
  view.add(<Node ref={world} scale={1.75} position={[-60, -330]} />);
  const W = world();
  const add = (n: any) => W.add(n);
  add(<Circle position={[230, -120]} size={() => 260 * sky()} fill={'#ffcf8a'} shadowBlur={140} shadowColor={'#ff9a50'} opacity={sky} />);
  // spotlights
  for (const x of [-260, 260]) {
    add(<Polygon points={[[x - 60, -960], [x + 60, -960], [x + 330, FLOOR], [x - 330, FLOOR]]} fill={'#ffffff'} opacity={0.06} />);
  }
  add(<Rect position={[0, FLOOR + 330]} size={[2000, 660]} fill={() => Color.lerp('#0b0c12', '#2a1e2a', sky())} />);
  add(<Rect position={[0, FLOOR + 2]} size={[1080, 4]} fill={'#5a5c6c'} />);
  // mat + standards + bar
  add(<Rect position={[BAR_X + 150, FLOOR - 36]} size={[260, 72]} radius={10} fill={'#2d4fae'} />);
  for (const dx of [-14, 70]) add(<Rect position={[BAR_X + dx, FLOOR - 135]} size={[8, 270]} fill={'#d6d6de'} />);
  const bar = createRef<Line>();
  add(<Line ref={bar} points={[[BAR_X - 14, 0], [BAR_X + 70, 0]]} y={BAR_Y} stroke={'#f0d23c'} lineWidth={7} lineCap={'round'} />);
  // header
  view.add(<Txt y={-880} text={'HOW MANY TIMES WOULD YOU TRY?'} fontFamily={'Inter'} fontWeight={800} fontSize={42} fill={'#eceef6'} letterSpacing={3} />);
  const n = createSignal(1);
  const gold = createSignal(0);
  view.add(<Txt y={-770} text={() => `TRY ${Math.round(n())}`} fontFamily={'Inter'} fontWeight={800} fontSize={() => 110 + 30 * gold()}
                fill={() => Color.lerp('#f6f6fa', '#f6c85a', gold())} letterSpacing={6} />);

  const him = createRef<Stick>();
  add(<Stick ref={him} scarf position={[-420, FLOOR - 113]} />);
  const h = him();

  // ---- helpers -------------------------------------------------------------------------------------------
  function* runTo(x: number, secs: number) {
    const ph = createSignal(0);
    h.legL(() => 0.75 * Math.sin(ph()));
    h.legR(() => -0.75 * Math.sin(ph()));
    h.kneeL(() => 0.2 + 1.1 * Math.max(0, Math.cos(ph() + 0.9)) ** 2);
    h.kneeR(() => 0.2 + 1.1 * Math.max(0, Math.cos(ph() + 0.9 + Math.PI)) ** 2);
    h.armL(() => -0.9 * Math.sin(ph()));
    h.armR(() => 0.9 * Math.sin(ph()));
    h.elbowL(1.4); h.elbowR(1.4);
    h.torso(0.25);
    const y0 = h.y();
    h.y(() => y0 - 10 * Math.abs(Math.sin(ph())));
    yield* all(h.x(x, secs, easeInOutSine), ph(Math.PI * 2 * secs * 2.6, secs, linear));
    h.y(y0);
  }
  function* setPose(p: Record<string, number>, secs: number, ease = easeInOutCubic) {
    yield* all(...Object.entries(p).map(([k, v]) => (h as any)[k](v, secs, ease)));
  }
  function* attempt(ok: boolean, speed = 1) {
    h.position([-420, FLOOR - 113]);
    h.torso(0); bar().rotation(0); bar().y(BAR_Y); bar().x(0);
    h.mouth(0); h.eyes(1);
    yield* runTo(BAR_X - 120, 0.9 / speed);
    // plant: crouch, then take off - flop over on his back
    yield* setPose({kneeL: 0.9, kneeR: 0.3, legL: 0.3, legR: -0.4, torso: 0.15, armL: -1.4, armR: -1.6}, 0.12 / speed, easeOutQuad);
    const up = ok ? 300 : 245;
    yield* all(
      h.x(BAR_X + 120, 0.7 / speed, linear),
      chain(h.y(FLOOR - 113 - up, 0.35 / speed, easeOutQuad), h.y(FLOOR - 120, 0.35 / speed, easeInCubic)),
      h.torso(-1.55, 0.5 / speed, easeInOutCubic),
      setPose({legL: 1.2, legR: 1.0, kneeL: 1.4, kneeR: 1.2, armL: 2.4, armR: 2.6, elbowL: 0.2, elbowR: 0.2}, 0.45 / speed),
      ok ? waitFor(0) : chain(waitFor(0.3 / speed),
        all(bar().rotation(28, 0.4 / speed, easeInCubic), bar().y(FLOOR - 10, 0.45 / speed, easeInCubic), bar().x(30, 0.45 / speed))),
    );
    if (!ok) {
      h.mouth(-1);
      yield* setPose({torso: -1.7, legL: 1.8, legR: 1.6, kneeL: 0.2, kneeR: 0.2}, 0.15 / speed, easeOutBack);
    }
  }

  // ---- the story -----------------------------------------------------------------------------------------
  yield* attempt(false);                                  // try 1: knocks the bar
  yield* waitFor(0.2);
  for (const target of [7, 23, 64, 99]) {                // quick tries
    yield* all(n(target, 0.6, easeOutQuad), attempt(false, 1.8));
  }
  n(100);
  yield* all(gold(1, 0.3, easeOutBack), sky(1, 1.6, easeInOutSine), attempt(true, 0.75));
  // lands, gets up, arms up
  h.mouth(1);
  yield* setPose({torso: 0, legL: 0.12, legR: -0.12, kneeL: 0, kneeR: 0, armL: 2.8, armR: -2.8, elbowL: 0.1, elbowR: -0.1}, 0.45, easeOutBack);
  yield* h.y(FLOOR - 113, 0.25, easeOutCubic);
  yield* waitFor(1.0);
});
