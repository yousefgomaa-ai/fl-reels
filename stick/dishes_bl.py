"""Blender side of "WILL IT FALL?" (LATER vs NOW, the same sink). Renders one panel as a PNG sequence.

    blender -b --python stick/dishes_bl.py -- later OUTDIR [frames: all | 0,30,90]

3D white figures with real light, a kitchen counter with a sink, dishes that stack day by day (LATER) or get
washed and put away (NOW). All motion comes from functions of t (seconds), so every frame is independent and the
last frame matches the first (the loop).
"""
import math
import os
import random
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SIDE, OUT = argv[0], argv[1]
FRAMES = argv[2] if len(argv) > 2 else "all"
FPS = 30
DUR = 17.0
NF = int(DUR * FPS)
U = 0.0062                      # metres per pose unit
HIP_Z = 113 * U
COUNTER_Z = 0.92
BASIN = (0.2, 0.7)
STACK_X, STACK_Y = 0.45, 0.45
MAN_X = -0.15
RACK_X = 1.3
TRASH = (-1.05, 0.0, 0.28)

# ---------------------------------------------------------------- timeline
DAYLEN = 0.92
DAY0 = -0.25                    # day 1 starts here so frame 0 is mid-reach
NDAYS = 14
T_FALL = DAY0 + 13 * DAYLEN + 0.95     # after the 14th placement
T_DUCK = T_FALL - 0.1
T_SWEEP0, T_SWEEP1 = 15.55, 16.25
T_RESTART = DUR + DAY0          # day 1 again, so t=DUR == t=0


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


def day_phase(t):
    """(day 1..14, phase 0..1 inside the day) - wraps at the end for the loop"""
    if t >= T_RESTART:
        t = t - DUR
    d = int((t - DAY0) // DAYLEN) + 1
    ph = ((t - DAY0) % DAYLEN) / DAYLEN
    return d, ph


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1040, 760
sc.render.resolution_percentage = 100
sc.render.fps = FPS
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 16
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.04
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 3
sc.cycles.diffuse_bounces = 2
sc.cycles.glossy_bounces = 2
sc.cycles.transmission_bounces = 2
sc.cycles.transparent_max_bounces = 4
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
vt = [v.identifier for v in type(sc.view_settings).bl_rna.properties["view_transform"].enum_items]
sc.view_settings.view_transform = "Filmic" if "Filmic" in vt else ("AgX" if "AgX" in vt else "Standard")


def mat(name, col, rough=0.45, emit=0.0, alpha=1.0, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = col
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    return m


WHITE = mat("white", (0.95, 0.95, 0.93, 1), 0.4, 0.09)
COUNTER = mat("counter", (0.32, 0.22, 0.15, 1), 0.6)
TOP = mat("top", (0.75, 0.74, 0.72, 1), 0.3)
BASIN_M = mat("basin", (0.08, 0.08, 0.09, 1), 0.25, metal=0.6)
STEEL = mat("steel", (0.7, 0.72, 0.75, 1), 0.2, metal=1.0)
FLOOR = mat("floor", (0.05, 0.045, 0.04, 1), 0.6)
WATER = mat("water", (0.55, 0.8, 1.0, 1), 0.05, emit=1.5, alpha=0.6)
SPARK = mat("spark", (1.0, 0.95, 0.7, 1), 0.3, emit=12)
CHAIR = mat("chair", (0.45, 0.3, 0.2, 1), 0.7)
TRASHM = mat("trash", (0.25, 0.27, 0.3, 1), 0.5, metal=0.4)
DISH_COLS = [(0.92, 0.9, 0.84, 1), (0.75, 0.85, 0.95, 1), (0.85, 0.93, 0.8, 1), (0.95, 0.85, 0.75, 1)]
DISH_M = [mat(f"dish{i}", c, 0.25) for i, c in enumerate(DISH_COLS)]
DIRT = mat("dirt", (0.35, 0.22, 0.1, 1), 0.7)
POT = mat("pot", (0.18, 0.18, 0.2, 1), 0.35, metal=0.8)


def add(o, m):
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def box(x0, x1, y0, y1, z0, z1, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.object
    o.scale = (x1 - x0, y1 - y0, z1 - z0)
    if bevel:
        bv = o.modifiers.new("b", "BEVEL")
        bv.width, bv.segments = bevel, 3
    return add(o, m)


# floor + counter + basin + faucet
bpy.ops.mesh.primitive_plane_add(size=40)
add(bpy.context.object, FLOOR)
box(-0.6, 2.0, 0.2, 0.85, 0.0, COUNTER_Z - 0.04, COUNTER, 0.01)
box(-0.65, 2.05, 0.15, 0.9, COUNTER_Z - 0.04, COUNTER_Z, TOP, 0.01)
box(BASIN[0], BASIN[1], 0.25, 0.7, COUNTER_Z - 0.035, COUNTER_Z + 0.002, BASIN_M)
bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.35, location=(0.45, 0.78, COUNTER_Z + 0.17))
add(bpy.context.object, STEEL)
bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.25, location=(0.45, 0.66, COUNTER_Z + 0.34),
                                    rotation=(math.radians(90), 0, 0))
add(bpy.context.object, STEEL)
bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.30, location=(0.45, 0.54, COUNTER_Z + 0.19))
water = add(bpy.context.object, WATER)
# dish rack (NOW) and trash bin (both)
if SIDE == "now":
    for k in range(5):
        box(RACK_X - 0.2 + k * 0.1, RACK_X - 0.19 + k * 0.1, 0.3, 0.6, COUNTER_Z, COUNTER_Z + 0.22, STEEL)
    box(RACK_X - 0.22, RACK_X + 0.24, 0.3, 0.6, COUNTER_Z, COUNTER_Z + 0.015, STEEL)
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.55, location=(TRASH[0], 0.1, 0.275))
add(bpy.context.object, TRASHM)

# ---------------------------------------------------------------- the figure
BONES = [("neck", "hip"), ("neck", "el"), ("el", "hl"), ("neck", "er"), ("er", "hr"), ("hip", "kl"),
         ("kl", "fl"), ("hip", "kr"), ("kr", "fr")]
LR = 0.045
limb_objs, joint_objs = [], {}
for _ in BONES:
    bpy.ops.mesh.primitive_cylinder_add(radius=LR, depth=1.0, vertices=24)
    limb_objs.append(add(bpy.context.object, WHITE))
for j in ("hip", "neck", "el", "hl", "er", "hr", "kl", "fl", "kr", "fr"):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=LR, segments=20, ring_count=10)
    joint_objs[j] = add(bpy.context.object, WHITE)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, segments=32, ring_count=16)
head = add(bpy.context.object, WHITE)


def place_limb(o, a, b, y):
    ax, az = a
    bx, bz = b
    L = max(1e-4, math.hypot(bx - ax, bz - az))
    o.location = ((ax + bx) / 2, y, (az + bz) / 2)
    o.rotation_euler = (0, math.atan2(bx - ax, bz - az), 0)
    o.scale = (1, 1, L)


STAND = {"head": (0, -150), "neck": (0, -108), "el": (-10, -58), "hl": (-14, -10), "er": (10, -58), "hr": (14, -10),
         "kl": (-9, 56), "fl": (-13, 113), "kr": (9, 56), "fr": (13, 113)}


def walk_legs(p, ph):
    p = dict(p)
    for side, off in (("l", 0.0), ("r", math.pi)):
        s = math.sin(ph + off)
        a = 0.42 * s
        kx, ky = 56 * math.sin(a), 56 * math.cos(a)
        bend = 0.1 + 0.6 * max(0.0, -math.cos(ph + off))
        p["k" + side] = (kx, ky)
        p["f" + side] = (kx + 57 * math.sin(a - bend), ky + 57 * math.cos(a - bend))
    return p


def ik(sh, target, l1=0.31, l2=0.30, down=1):
    """2-bone IK in x-z; returns elbow, hand (metres)."""
    dx, dz = target[0] - sh[0], target[1] - sh[1]
    d = math.hypot(dx, dz)
    d2 = min(d, l1 + l2 - 1e-3)
    base = math.atan2(dz, dx)
    cosa = clamp((l1 * l1 + d2 * d2 - l2 * l2) / (2 * l1 * d2), -1, 1)
    a = base - down * math.acos(cosa)
    el = (sh[0] + l1 * math.cos(a), sh[1] + l1 * math.sin(a))
    hand = (sh[0] + d2 / d * dx if d > 0 else sh[0], sh[1] + d2 / d * dz if d > 0 else sh[1])
    return el, hand


def figure(pose, hipx, hipz, y=-0.15, right=None, left=None, lean=0.0):
    """pose in units (y down) placed with its hip at (hipx, hipz) metres; optional IK targets for the hands."""
    P = {}
    c, s = math.cos(lean), math.sin(lean)
    for k, (px, py) in pose.items():
        x, z = px * U, -py * U
        if k in ("head", "neck", "el", "hl", "er", "hr"):
            x, z = x * c + z * s, -x * s + z * c
        P[k] = (hipx + x, hipz + z)
    P["hip"] = (hipx, hipz)
    for side, tgt in (("r", right), ("l", left)):
        if tgt:
            el, hd = ik(P["neck"], tgt, down=1)
            P["e" + side], P["h" + side] = el, hd
    for o, (a, b) in zip(limb_objs, BONES):
        place_limb(o, P[a], P[b], y)
    for j, o in joint_objs.items():
        o.location = (P[j][0], y, P[j][1])
    hx, hz = P["head"]
    head.location = (hx, y, hz)
    return P


# ---------------------------------------------------------------- dishes
random.seed(4)
KINDS = []
for d in range(NDAYS):
    for k in range(2):
        r = random.random()
        KINDS.append("pot" if (d < 3 and k == 0 and r < 0.6) else ("bowl" if r < 0.35 else ("mug" if r > 0.88 else
                                                                                           "plate")))
H = {"plate": 0.035, "bowl": 0.075, "mug": 0.1, "pot": 0.15}
R = {"plate": 0.14, "bowl": 0.105, "mug": 0.05, "pot": 0.12}
items = []
for i, kd in enumerate(KINDS):
    if kd == "bowl":
        bpy.ops.mesh.primitive_cone_add(radius1=0.075, radius2=R[kd], depth=H[kd], vertices=32)
    else:
        bpy.ops.mesh.primitive_cylinder_add(radius=R[kd], depth=H[kd], vertices=32)
    o = add(bpy.context.object, POT if kd == "pot" else DISH_M[i % len(DISH_M)])
    if kd != "pot" and SIDE == "later":
        o.data.materials.append(DIRT)
    items.append(o)
# a smear of food on the dirty ones (LATER): a flat brown disc on top of each
smears = []
for i, kd in enumerate(KINDS):
    bpy.ops.mesh.primitive_cylinder_add(radius=R[kd] * 0.55, depth=0.006, vertices=20)
    smears.append(add(bpy.context.object, DIRT))
# shards for the crash
shards = []
for i in range(len(KINDS)):
    group = []
    for k in range(3):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.02, vertices=3)
        group.append(add(bpy.context.object, DISH_M[i % len(DISH_M)]))
    shards.append(group)
stack_base_z = COUNTER_Z - 0.03
OFFS = [(random.uniform(-0.025, 0.025)) for _ in KINDS]
ZS = []
z = stack_base_z
for kd in KINDS:
    ZS.append(z + H[kd] / 2)
    z += H[kd]
TOTAL_H = z - stack_base_z

# chair (LATER, from day 11), spark balls (NOW)
bpy.ops.mesh.primitive_cube_add(size=1)
chair = bpy.context.object
chair.scale = (0.42, 0.42, 0.06)
add(chair, CHAIR)
chair_legs = []
for k in range(4):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.45)
    chair_legs.append(add(bpy.context.object, CHAIR))
sparks = []
for k in range(6):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.018, segments=12, ring_count=6)
    sparks.append(add(bpy.context.object, SPARK))
# a mug of coffee for NOW's relaxed end
bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.09, vertices=24)
coffee = add(bpy.context.object, DISH_M[3])

# ---------------------------------------------------------------- lights + camera
for x, e in ((-0.2, 700), (1.0, 900)):
    bpy.ops.object.light_add(type="SPOT", location=(x, -0.8, 5.6))
    l = bpy.context.object
    l.data.energy = e
    l.data.color = (1.0, 0.86, 0.66)
    l.data.spot_size = math.radians(52)
    l.data.spot_blend = 0.6
    l.data.shadow_soft_size = 0.4
    l.rotation_euler = (math.radians(8), 0, 0)
bpy.ops.object.light_add(type="AREA", location=(0.6, -6, 2.4))
fl = bpy.context.object
fl.data.energy = 90
fl.data.size = 5
fl.rotation_euler = (math.radians(75), 0, 0)
bpy.ops.object.camera_add(location=(0.35, -6.2, 1.58), rotation=(math.radians(89), 0, 0))
cam = bpy.context.object
cam.data.lens = 48
sc.camera = cam

HIDE = (0, 0, -50)


def hide(o):
    o.location = HIDE


# ---------------------------------------------------------------- state per frame
def n_placed(t):
    """items on the stack (LATER) / washed so far (NOW)"""
    if t >= T_RESTART:
        d, ph = day_phase(t)
        return 0 if ph < 0.38 else 2
    d, ph = day_phase(t)
    if d > NDAYS:
        return 2 * NDAYS
    return 2 * (d - 1) + (2 if ph >= 0.38 else 0)


def sway(t, n):
    if n == 0:
        return 0.0
    A = 0.0009 * n ** 1.6
    imp = 0.0
    d, ph = day_phase(t)
    if ph >= 0.38:
        imp = 0.04 * (n / 28) * math.exp(-(ph - 0.38) * DAYLEN * 4) * math.sin((ph - 0.38) * DAYLEN * 18)
    return A * math.sin(t * 2 * math.pi * 0.85) + imp


def stack_pose(i, n, th):
    """position + tilt of item i in a stack of n tilted by th (bends more towards the top)"""
    h = ZS[i] - stack_base_z
    k = h / max(TOTAL_H, 1e-3)
    ang = th * (0.4 + 0.6 * k)
    x = STACK_X + OFFS[i] + math.sin(th) * h * (0.4 + 0.6 * k)
    z = stack_base_z + h * math.cos(ang)
    return x, z, ang


def later(t):
    n = n_placed(t)
    d, ph = day_phase(t)
    th = sway(t, n) if t < T_FALL else 0
    on_chair = (d >= 11 and t < T_DUCK) and t < T_RESTART
    hipz = HIP_Z + (0.47 if on_chair else 0.0)
    top = stack_base_z + sum(H[KINDS[j]] for j in range(n))
    # the chair
    if on_chair or (T_DUCK <= t < T_SWEEP1):
        k = 0.0 if t < T_FALL else smooth(prog(t, T_FALL, T_FALL + 0.5))
        cx = MAN_X - 0.6 * k
        chair.location = (cx, -0.15, 0.47)
        chair.rotation_euler = (0, -1.4 * k, 0)
        for j, lg in enumerate(chair_legs):
            lx = (-0.18 if j % 2 else 0.18)
            ly = -0.15 + (-0.18 if j < 2 else 0.18)
            lg.location = (cx + lx * math.cos(1.4 * k), ly, 0.235 + lx * math.sin(1.4 * k))
            lg.rotation_euler = (0, -1.4 * k, 0)
        if T_SWEEP0 <= t < T_SWEEP1:
            u = smooth(prog(t, T_SWEEP0, T_SWEEP1))
            chair.location = (lerp(cx, TRASH[0], u), -0.15, lerp(0.47, 0.5, u))
            chair.scale = (0.42 * (1 - u) + 1e-3, 0.42 * (1 - u) + 1e-3, 0.06)
            for lg in chair_legs:
                hide(lg)
    else:
        hide(chair)
        for lg in chair_legs:
            hide(lg)
    # the man
    if t < T_DUCK or t >= T_RESTART:
        if ph < 0.38:
            k = smooth(ph / 0.38)
            tgt = (lerp(MAN_X + 0.25, STACK_X - 0.08, k), lerp(hipz + 0.55, top + 0.12, k))
        elif ph < 0.7:
            k = smooth((ph - 0.38) / 0.32)
            tgt = (lerp(STACK_X - 0.08, MAN_X + 0.25, k), lerp(top + 0.06, hipz + 0.5, k))
        else:
            tgt = None
        if d >= 13 and ph >= 0.7 and t < T_DUCK:
            # holds the wobbling tower steady with both hands
            P = figure(STAND, MAN_X, hipz, right=(STACK_X - 0.1, top - 0.35), left=(STACK_X - 0.12, top - 0.55))
        else:
            P = figure(STAND, MAN_X, hipz, right=tgt)
        hand = P["hr"]
    elif t < T_SWEEP0:
        k = smooth(prog(t, T_DUCK, T_DUCK + 0.35))
        duck = {"head": (30, -92), "neck": (20, -64), "el": (50, -110), "hl": (20, -130), "er": (60, -104),
                "hr": (30, -124), "kl": (40, 10), "fl": (0, 113), "kr": (50, 20), "fr": (20, 113)}
        P = figure(duck if k > 0.5 else STAND, lerp(MAN_X, MAN_X - 0.45, k), lerp(hipz, HIP_Z - 0.18, k))
        hand = None
    else:
        k = smooth(prog(t, T_SWEEP0, T_SWEEP1))
        sweep = dict(STAND, el=(-30, -60), hl=(-60, -20), er=(-20, -60), hr=(-50, -16))
        P = figure(walk_legs(sweep, t * 10) if k < 1 else STAND, lerp(MAN_X - 0.45, MAN_X, smooth(prog(t, T_SWEEP1 - 0.2,
                                                                                                    T_RESTART))),
                   HIP_Z)
        hand = None
    # the dishes
    carried = []
    if (t < T_DUCK or t >= T_RESTART) and ph < 0.38 and d <= NDAYS:
        first = 0 if t >= T_RESTART else 2 * (d - 1)
        carried = [first, first + 1]
    for i, o in enumerate(items):
        sm = smears[i]
        for s_ in shards[i]:
            hide(s_)
        if i in carried and hand:
            z0 = hand[1] - 0.02 + (0 if i == carried[0] else H[KINDS[carried[0]]])
            o.location = (hand[0] + 0.12, STACK_Y, z0 + H[KINDS[i]] / 2)
            o.rotation_euler = (0, 0, 0)
            o.scale = (1, 1, 1)
        elif i < n and t < T_FALL:
            x, z, ang = stack_pose(i, n, th)
            o.location = (x, STACK_Y, z)
            o.rotation_euler = (0, ang, 0)
            o.scale = (1, 1, 1)
        elif i < n and t < T_SWEEP1 and t < T_RESTART:
            # the fall: ballistic from the stack, then shatter on the floor
            rnd = random.Random(i * 7 + 1)
            x0, z0, a0 = stack_pose(i, n, 0.12)
            delay = (1 - (ZS[i] - stack_base_z) / TOTAL_H) * 0.35
            u = max(0.0, t - T_FALL - delay)
            vx = rnd.uniform(-1.4, 2.2) * (0.5 + (ZS[i] - stack_base_z) / TOTAL_H)
            vz = rnd.uniform(0.2, 1.6)
            spin = rnd.uniform(-9, 9)
            x = x0 + vx * u
            z = z0 + vz * u - 4.9 * u * u
            rest = 0.01 + H[KINDS[i]] / 2
            landed = z <= rest
            if landed:
                tl = (vz + math.sqrt(vz * vz + 4 * 4.9 * max(0, z0 - rest))) / (2 * 4.9)
                x = x0 + vx * tl
                z = rest
            ys = STACK_Y - 0.25 * min(u, 1.0) * rnd.uniform(0.5, 1.5)
            if T_SWEEP0 <= t:
                k2 = smooth(prog(t, T_SWEEP0, T_SWEEP1))
                x, z = lerp(x, TRASH[0], k2), lerp(z, TRASH[2] + 0.3, k2)
            if landed and KINDS[i] != "pot":
                hide(o)
                for j, s_ in enumerate(shards[i]):
                    a = j * 2.1 + i
                    sx, sz = x + 0.12 * math.cos(a), 0.012
                    if T_SWEEP0 <= t:
                        k2 = smooth(prog(t, T_SWEEP0, T_SWEEP1))
                        sx, sz = lerp(sx, TRASH[0], k2), lerp(sz, TRASH[2] + 0.3, k2)
                        s_.scale = (1 - k2 + 1e-3,) * 3
                    else:
                        s_.scale = (1, 1, 1)
                    s_.location = (sx, ys + 0.1 * math.sin(a), sz)
                    s_.rotation_euler = (0, 0, a)
            else:
                o.location = (x, ys, z)
                o.rotation_euler = (0, a0 + (spin * u if not landed else 1.57 * (i % 2)), 0)
                k2 = smooth(prog(t, T_SWEEP0, T_SWEEP1)) if t >= T_SWEEP0 else 0
                o.scale = (1 - k2 + 1e-3,) * 3
        else:
            hide(o)
        if SIDE == "later" and o.location[2] > -10 and KINDS[i] != "pot":
            sm.location = (o.location[0], o.location[1], o.location[2] + H[KINDS[i]] / 2 + 0.002)
            sm.rotation_euler = o.rotation_euler
            sm.scale = o.scale
        else:
            hide(sm)
    hide(water)
    hide(coffee)
    for s_ in sparks:
        hide(s_)


def now(t):
    d, ph = day_phase(t)
    end = T_DUCK <= t < T_RESTART
    for i, o in enumerate(items):
        hide(o)
        hide(smears[i])
        for s_ in shards[i]:
            hide(s_)
    hide(chair)
    for lg in chair_legs:
        hide(lg)
    for s_ in sparks:
        hide(s_)
    hide(coffee)
    hide(water)
    first = 2 * ((d - 1) % NDAYS)
    if not end:
        if ph < 0.45:
            # wash under the tap
            water.location = (0.45, 0.54, COUNTER_Z + 0.19)
            sc_ = 6 * math.sin(t * 40)
            P = figure(STAND, MAN_X + 0.05, HIP_Z, right=(STACK_X - 0.12 + 0.03 * math.sin(t * 30), COUNTER_Z + 0.12),
                       left=(STACK_X - 0.16, COUNTER_Z + 0.08 + 0.02 * math.cos(t * 30)))
            for k2, i in enumerate((first, first + 1)):
                o = items[i]
                o.location = (STACK_X - 0.02, STACK_Y - 0.2, COUNTER_Z + 0.1 + k2 * 0.05)
                o.rotation_euler = (0, 0.6 + 0.1 * math.sin(t * 30), 0)
                o.scale = (1, 1, 1)
        elif ph < 0.85:
            # step to the rack, put them in, step back
            k = smooth((ph - 0.45) / 0.4)
            hx = MAN_X + 0.05 + 0.6 * math.sin(math.pi * k)
            reach = k > 0.35 and k < 0.75
            P = figure(walk_legs(STAND, t * 12), hx, HIP_Z,
                       right=(RACK_X - 0.15, COUNTER_Z + 0.25) if reach else None)
            for k2, i in enumerate((first, first + 1)):
                o = items[i]
                if k < 0.55:
                    hand = P["hr"]
                    o.location = (hand[0] + 0.08, -0.05, hand[1] + k2 * 0.04)
                    o.rotation_euler = (0, 0.3, 0)
                else:
                    o.location = (RACK_X - 0.1 + k2 * 0.16, 0.45, COUNTER_Z + 0.16)
                    o.rotation_euler = (0, 1.45, 0)
                o.scale = (1, 1, 1)
            if k > 0.5:
                for j, s_ in enumerate(sparks):
                    a = j * 1.05 + t * 3
                    r = 0.18 + 0.1 * (k - 0.5)
                    s_.location = (RACK_X + r * math.cos(a), 0.3, COUNTER_Z + 0.25 + r * math.sin(a))
        else:
            P = figure(STAND, MAN_X + 0.05, HIP_Z)
            for k2, i in enumerate((first, first + 1)):
                o = items[i]
                o.location = (RACK_X - 0.1 + k2 * 0.16, 0.45, COUNTER_Z + 0.16)
                o.rotation_euler = (0, 1.45, 0)
                o.scale = (1, 1, 1)
    else:
        # the sink is clean: he leans on the counter with a coffee, sipping
        sip = max(0.0, math.sin(t * 2.2))
        P = figure(STAND, MAN_X + 0.05, HIP_Z, right=(MAN_X + 0.32, 1.35 + 0.18 * sip), left=(MAN_X + 0.4, 0.98))
        hx, hz = P["hr"]
        coffee.location = (hx + 0.04, -0.15, hz + 0.05)
        if t < T_DUCK + 0.6:
            for i in (2 * NDAYS - 2, 2 * NDAYS - 1):
                o = items[i]
                o.location = (RACK_X - 0.1 + (i % 2) * 0.16, 0.45, COUNTER_Z + 0.16)
                o.rotation_euler = (0, 1.45, 0)
                o.scale = (1, 1, 1)


def update(t):
    (later if SIDE == "later" else now)(t)


os.makedirs(OUT, exist_ok=True)
frames = range(NF) if FRAMES == "all" else [int(round(float(x) * FPS)) for x in FRAMES.split(",")]
for f in frames:
    update(f / FPS)
    sc.render.filepath = os.path.join(OUT, f"{f:04d}.png")
    bpy.ops.render.render(write_still=True)
