import {Circle, Line, Node, Polygon, Rect, Txt} from '@motion-canvas/2d';
import {Color, createRef, createSignal, easeOutBack, SimpleSignal, Vector2} from '@motion-canvas/core';
import {View2D} from '@motion-canvas/2d';
import {Stick} from './stick';

export const FLOOR = 300;
export const L = 2.4;          // seconds per situation
export const T_S = 1.6;        // the success moment inside it

/** The Same Wall look: dark stage, light cones from above, a glossy floor, dust, the TRY header. */
export function stage(view: View2D, opts: {scale?: number; x?: number; y?: number} = {}) {
  const sky = createSignal(0);
  view.add(<Rect size={[1080, 1920]} fill={() => Color.lerp('#0a0c14', '#3a2e5c', sky())} />);
  view.add(<Circle position={[220, -260]} size={() => 300 * sky()} fill={'#ffcf8a'} shadowBlur={160} shadowColor={'#ff9a50'} opacity={sky} />);
  const world = createRef<Node>();
  view.add(<Node ref={world} scale={opts.scale ?? 1.7} position={[opts.x ?? 0, opts.y ?? -300]} />);
  const w = world();
  for (const x of [-300, 0, 300]) {
    w.add(<Line closed points={[[x - 50, -900], [x + 50, -900], [x + 300, FLOOR], [x - 300, FLOOR]]} fill={'#c8d2ff'} opacity={x === 0 ? 0.07 : 0.045} />);
  }
  // glossy floor
  w.add(<Rect position={[0, FLOOR + 400]} size={[3000, 800]} fill={() => Color.lerp('#0d0e15', '#241a26', sky())} />);
  w.add(<Rect position={[0, FLOOR + 60]} size={[1600, 120]} fill={'#ffffff'} opacity={0.035} radius={60} />);
  w.add(<Rect position={[0, FLOOR + 1]} size={[3000, 3]} fill={'#62647a'} />);
  // dust in the light
  for (let i = 0; i < 26; i++) {
    const x0 = ((i * 97) % 600) - 300, y0 = -700 + ((i * 211) % 900);
    w.add(<Circle size={4} fill={'#ffe8c8'} opacity={0.35} position={[x0, y0]} />);
  }
  // header
  view.add(<Txt y={-880} text={'HOW MANY TIMES WOULD YOU TRY?'} fontFamily={'Inter'} fontWeight={800} fontSize={42} fill={'#eceef6'} letterSpacing={3} />);
  const n = createSignal(1);
  const gold = createSignal(0);
  view.add(<Txt y={-770} text={() => `TRY ${Math.round(n())}`} fontFamily={'Inter'} fontWeight={800} fontSize={() => 112 + 26 * gold()}
                fill={() => Color.lerp('#f6f6fa', '#f6c85a', gold())} letterSpacing={6} />);
  const flash = createSignal(0);
  view.add(<Rect size={[1080, 1920]} fill={'#ffdc8c'} opacity={() => 0.18 * flash()} />);
  return {world: w, n, gold, sky, flash};
}

/** soft shadow under a figure */
export function shadow(w: Node, x: () => number, k: () => number = () => 1) {
  w.add(<Circle position={() => new Vector2(x(), FLOOR + 4)} size={() => [120 * k(), 18 * k()]} fill={'#000000'} opacity={0.45} />);
}

export function* success(s: {n: SimpleSignal<number>; gold: SimpleSignal<number>; flash: SimpleSignal<number>}, total: number) {
  s.n(total);
  s.flash(1);
  yield* s.gold(1, 0.25, easeOutBack);
  yield* s.flash(0, 0.2);
}
