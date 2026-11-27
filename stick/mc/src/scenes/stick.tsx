import {Circle, Line, Node, NodeProps, Polygon} from '@motion-canvas/2d';
import {createSignal, SimpleSignal, Vector2} from '@motion-canvas/core';

/** A rigged stick figure: forward kinematics, angles in radians measured from "straight down", + = forward. */
export interface StickProps extends NodeProps {
  body?: string;
  scarf?: boolean;
}

const UP = 104, HEAD = 44, ARM1 = 42, ARM2 = 40, LEG1 = 56, LEG2 = 57;

export class Stick extends Node {
  public readonly torso = createSignal(0);
  public readonly headTilt = createSignal(0);
  public readonly armL = createSignal(0.25);
  public readonly elbowL = createSignal(0.2);
  public readonly armR = createSignal(-0.25);
  public readonly elbowR = createSignal(0.2);
  public readonly legL = createSignal(0.12);
  public readonly kneeL = createSignal(0.0);
  public readonly legR = createSignal(-0.12);
  public readonly kneeR = createSignal(0.0);
  public readonly mouth = createSignal(0);     // -1 frown .. 1 smile
  public readonly eyes = createSignal(1);      // 1 open .. 0 closed

  private dir(a: number, len: number) {
    return new Vector2(Math.sin(a) * len, Math.cos(a) * len);
  }
  private neck = () => this.dir(this.torso() + Math.PI, UP);
  private headPos = () => this.neck().add(this.dir(this.torso() + this.headTilt() + Math.PI, HEAD));
  private limb(base: () => Vector2, a: () => number, b: () => number, l1: number, l2: number, knee = false) {
    const j = () => base().add(this.dir(a(), l1));
    const e = () => j().add(this.dir(a() + (knee ? -b() : b()), l2));
    return [base, j, e];
  }

  public constructor(props?: StickProps) {
    super({...props});
    const col = props?.body ?? '#eceef4';
    const ink = '#15161c';
    const hip = () => Vector2.zero;
    const legs = [this.limb(hip, this.legL, this.kneeL, LEG1, LEG2, true), this.limb(hip, this.legR, this.kneeR, LEG1, LEG2, true)];
    const arms = [this.limb(this.neck, this.armL, this.elbowL, ARM1, ARM2), this.limb(this.neck, this.armR, this.elbowR, ARM1, ARM2)];
    const parts: [() => Vector2, () => Vector2, () => Vector2][] = [...legs, ...arms] as any;
    for (const w of [27, 20]) {
      for (const [a, b, c] of parts) {
        this.add(<Line points={() => [a(), b(), c()]} stroke={w > 21 ? ink : col} lineWidth={w} lineCap={'round'} lineJoin={'round'} />);
      }
      this.add(<Line points={() => [hip(), this.neck()]} stroke={w > 21 ? ink : col} lineWidth={w} lineCap={'round'} />);
    }
    this.add(<Circle position={this.headPos} size={66} fill={col} stroke={ink} lineWidth={3.5} />);
    // face, turned a little toward +x
    const f = () => this.headPos().add(new Vector2(7, 4));
    this.add(<Circle position={() => f().add(new Vector2(-11, -6))} width={7} height={() => 1 + 8 * this.eyes()} fill={ink} />);
    this.add(<Circle position={() => f().add(new Vector2(11, -6))} width={7} height={() => 1 + 8 * this.eyes()} fill={ink} />);
    this.add(<Line points={() => {
      const c = f().add(new Vector2(0, 12));
      const m = this.mouth();
      return [c.add(new Vector2(-9, -3 * m)), c.add(new Vector2(0, 4 * m)), c.add(new Vector2(9, -3 * m))];
    }} stroke={ink} lineWidth={3.5} lineCap={'round'} radius={8} />);
    if (props?.scarf) {
      this.add(<Polygon position={() => this.neck().add(new Vector2(0, 4))} sides={20} size={[42, 22]} fill={'#d62c2c'} />);
      this.add(<Line points={() => [this.neck(), this.neck().add(new Vector2(-46, 26)), this.neck().add(new Vector2(-30, 40))]}
                     closed fill={'#d62c2c'} />);
    }
  }
}
