#!/usr/bin/env python3
"""Motion capture (CMU BVH, Bruce Hahne's 2010 MotionBuilder-friendly conversion) -> our stick figure.

load(path) parses the skeleton + frames and runs forward kinematics.
Clip.pts(t) returns the joint dict our figure() draws (head, neck, hip, elbows, hands, knees, feet), retargeted to
OUR bone lengths (so every clip draws the same character), seen from the side, in screen pixels.
"""
import math
import os
import re

import numpy as np

CMU = os.environ.get("CMU_BVH", "/home/user/una-dinosauria/cmu-mocap/data")


def _rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "X":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "Y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _rots(axis, deg):
    """vectorised over frames"""
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    o, z = np.ones_like(a), np.zeros_like(a)
    if axis == "X":
        m = [[o, z, z], [z, c, -s], [z, s, c]]
    elif axis == "Y":
        m = [[c, z, s], [z, o, z], [-s, z, c]]
    else:
        m = [[c, -s, z], [s, c, z], [z, z, o]]
    return np.stack([np.stack(r, -1) for r in m], -2)          # (F, 3, 3)


def load(path):
    if not os.path.isabs(path):
        path = os.path.join(CMU, path[:2].zfill(3) if "/" not in path else "", path)
    txt = open(path).read()
    head, motion = txt.split("MOTION")
    tokens = re.findall(r"[{}]|[^\s{}]+", head)
    joints, stack, i = [], [], 0
    cur = None
    while i < len(tokens):
        tk = tokens[i]
        if tk in ("ROOT", "JOINT"):
            cur = {"name": tokens[i + 1], "parent": stack[-1] if stack else -1, "chan": [], "end": False}
            joints.append(cur)
            i += 2
        elif tk == "End":
            cur = {"name": joints[stack[-1]]["name"] + "_end", "parent": stack[-1], "chan": [], "end": True}
            joints.append(cur)
            i += 2
        elif tk == "{":
            stack.append(len(joints) - 1)
            i += 1
        elif tk == "}":
            stack.pop()
            i += 1
        elif tk == "OFFSET":
            cur["off"] = np.array([float(tokens[i + 1]), float(tokens[i + 2]), float(tokens[i + 3])])
            i += 4
        elif tk == "CHANNELS":
            n = int(tokens[i + 1])
            cur["chan"] = tokens[i + 2:i + 2 + n]
            i += 2 + n
        else:
            i += 1
    lines = motion.strip().splitlines()
    nf = int(lines[0].split()[1])
    ft = float(lines[1].split()[2])
    data = np.array([[float(v) for v in l.split()] for l in lines[2:2 + nf]])
    # forward kinematics
    F = len(data)
    pos = np.zeros((len(joints), F, 3))
    rot = np.zeros((len(joints), F, 3, 3))
    col = 0
    for j, jt in enumerate(joints):
        R = np.broadcast_to(np.eye(3), (F, 3, 3)).copy()
        p = np.zeros((F, 3))
        for ch in jt["chan"]:
            v = data[:, col]
            col += 1
            if ch.endswith("position"):
                p[:, "XYZ".index(ch[0])] = v
            else:
                R = R @ _rots(ch[0], v)
        if jt["parent"] < 0:
            pos[j] = jt["off"] + p
            rot[j] = R
        else:
            pr = rot[jt["parent"]]
            pos[j] = pos[jt["parent"]] + np.einsum("fij,j->fi", pr, jt["off"])
            rot[j] = pr @ R
    names = {jt["name"]: k for k, jt in enumerate(joints)}
    return Clip(pos, names, ft)


# our skeleton (pixels at scale 1.0, same as the rest of the engine)
SEG = {"neck": 104, "head": 44, "el": 42, "hl": 40, "kl": 56, "fl": 57}


class Clip:
    def __init__(self, pos, names, ft):
        self.pos, self.names, self.ft = pos, names, ft
        self.n = pos.shape[1]
        self.dur = self.n * ft
        j = lambda k: self.pos[self.names[k]]   # noqa
        self.J = {"hip": j("Hips"), "neck": j("Neck1") if "Neck1" in names else j("Neck"), "headtop": j("Head_end") if "Head_end" in names else j("Head"),
                  "el": j("LeftForeArm"), "hl": j("LeftHand"), "er": j("RightForeArm"), "hr": j("RightHand"),
                  "shl": j("LeftArm"), "shr": j("RightArm"),
                  "kl": j("LeftLeg"), "fl": j("LeftFoot"), "kr": j("RightLeg"), "fr": j("RightFoot"),
                  "hipl": j("LeftUpLeg"), "hipr": j("RightUpLeg"), "toel": j("LeftToeBase"), "toer": j("RightToeBase")}
        # side view: the horizontal axis the hips travel along the most (or forward of the body if they stand still)
        hz = self.J["hip"][:, [0, 2]]
        d = hz[-1] - hz[0]
        if np.linalg.norm(d) < 5:
            fwd = (self.J["toel"] - self.J["fl"])[:, [0, 2]].mean(0)
            d = fwd
        self.ax = d / (np.linalg.norm(d) + 1e-9)
        self.ground = min(self.J["toel"][:, 1].min(), self.J["toer"][:, 1].min(), self.J["fl"][:, 1].min(), self.J["fr"][:, 1].min())
        leg = np.linalg.norm(self.J["kl"][0] - self.J["hipl"][0]) + np.linalg.norm(self.J["fl"][0] - self.J["kl"][0])
        self.px = (SEG["kl"] + SEG["fl"]) / leg          # mocap units -> our pixels

    def frame(self, t, loop=False):
        f = t / self.ft
        if loop:
            f = f % (self.n - 1)
        return min(max(f, 0), self.n - 1.001)

    def _2d(self, key, f):
        i = int(f)
        a = f - i
        v = self.J[key][i] * (1 - a) + self.J[key][i + 1] * a
        x = (v[0] * self.ax[0] + v[2] * self.ax[1])
        return np.array([x, v[1]])

    def pts(self, t, x0=0.0, floor=0.0, scale=1.0, facing=1, loop=False, x_lock=None):
        """joint dict in screen pixels. x0/floor place the clip's start / ground; scale = our S"""
        f = self.frame(t, loop)
        P = {k: self._2d(k, f) for k in self.J}
        start = self._2d("hip", 0.0)
        k = self.px * scale

        def scr(v):
            return np.array([x0 + facing * (v[0] - start[0]) * k, floor - (v[1] - self.ground) * k])
        hip = scr(P["hip"])
        if x_lock is not None:
            hip[0] = x_lock
        out = {"hip": tuple(hip)}

        def dirv(a, b):
            d = np.array([facing * (P[b][0] - P[a][0]), -(P[b][1] - P[a][1])])
            n = np.linalg.norm(d)
            return d / n if n > 1e-6 else np.array([0.0, 1.0])
        neck = hip + dirv("hip", "neck") * SEG["neck"] * scale
        out["neck"] = tuple(neck)
        out["head"] = tuple(neck + dirv("neck", "headtop") * SEG["head"] * scale)
        for side in "lr":
            e = neck + dirv("sh" + side, "e" + side) * SEG["el"] * scale
            h = e + dirv("e" + side, "h" + side) * SEG["hl"] * scale
            kn = hip + dirv("hip" + side, "k" + side) * SEG["kl"] * scale
            ft = kn + dirv("k" + side, "f" + side) * SEG["fl"] * scale
            out["e" + side], out["h" + side], out["k" + side], out["f" + side] = tuple(e), tuple(h), tuple(kn), tuple(ft)
        # keep the retargeted feet on the floor: our bone lengths differ slightly from the actor's
        lowest = max(out["fl"][1], out["fr"][1])
        raw_low = max(scr(P["fl"])[1], scr(P["fr"])[1])
        dy = raw_low - lowest
        if abs(dy) > 0:
            out = {kk: (vx, vy + dy) for kk, (vx, vy) in out.items()}
        return out


if __name__ == "__main__":
    import sys
    c = load(sys.argv[1])
    print(c.n, "frames", round(c.dur, 2), "s", "ax", c.ax, "px", round(c.px, 2))
