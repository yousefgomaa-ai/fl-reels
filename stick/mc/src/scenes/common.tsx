import {all, chain, easeInCubic, easeInQuad, easeOutQuad, linear, loop, waitFor, createSignal} from '@motion-canvas/core';
import {Stick, STAND} from './stick';
import {L, T_S} from './stage';

/** counter 1 -> N-1 while it keeps failing */
export function* countUp(n: any, N: number) {
  n(1);
  yield* n(N - 1, T_S, easeInQuad);
}

/** a run/walk cycle on a Stick for `secs` */
export function* cycle(h: Stick, secs: number, rate = 2.6, amp = 0.75) {
  const ph = createSignal(0);
  h.legL(() => amp * Math.sin(ph()));
  h.legR(() => -amp * Math.sin(ph()));
  h.kneeL(() => 0.2 + 1.1 * amp * Math.max(0, Math.cos(ph() + 0.9)) ** 2);
  h.kneeR(() => 0.2 + 1.1 * amp * Math.max(0, Math.cos(ph() + 0.9 + Math.PI)) ** 2);
  h.armL(() => -1.1 * amp * Math.sin(ph()));
  h.armR(() => 1.1 * amp * Math.sin(ph()));
  h.elbowL(1.3); h.elbowR(1.3);
  yield* ph(Math.PI * 2 * secs * rate, secs, linear);
  h.set({legL: h.legL(), legR: h.legR(), kneeL: h.kneeL(), kneeR: h.kneeR(), armL: h.armL(), armR: h.armR()});
}

export function* exact(story: any) {
  yield* all(story, waitFor(L));
}
