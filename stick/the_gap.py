#!/usr/bin/env python3
"""THE GAP - Overthinker vs Doer, one scene, one goal, three different tries, 22.4 s, loops on itself.

Two cliffs at night; on the far one a chest glows. The overthinker sits on a rock: "TOO FAR."
Try 1: the doer runs and jumps - short, into the river far below; he climbs back up ("TOLD YOU.").
Try 2: one plank pushed over the gap - too short, it tips and takes him down ("JUST GIVE UP." - the phone comes out).
Try 3: he sits and thinks - "?", then a light bulb; he ties two planks with the rope, pushes the long plank across,
walks over and opens the chest: gold light. The overthinker looks up from his phone: "LUCKY."
"HE CALLED IT LUCK. / IT WAS TRY NUMBER 3."  TRIES 0 : 3 at the top.

    python3 stick/the_gap.py stick/the-gap.mp4
    ONLY_FRAMES=0,2.2,3.0,4.2,6.6,7.3,10.4,11.2,12.4,13.4,14.3,15.6,16.4,19.5 python3 stick/the_gap.py /tmp/gap
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import ai_job as AJ  # noqa
import game_spend as GS  # noqa
from perfect_wave import (MONO, clamp, env, font, in_quad, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          out_cubic, prog, rot, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 75
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 7 * BAR                           # 22.4 s
NF = int(round(DUR * FPS))
XFADE = 0.5
SC = AJ.SC
INK = AJ.INK
DOER, DOER_FAR, OT, OT_FAR = AJ.DOER, AJ.DOER_FAR, AJ.OT, AJ.OT_FAR
GOLD = (255, 200, 80)

# ---------------------------------------------------------------- the set
CT = 1180                               # the top of both cliffs
LE, RE = 380, 700                       # left cliff's edge, right cliff's edge
RIVER = 1800
CHEST_X = 915
ROCK_X = 92
PLANK_L = 230
STAND_Y = CT - 113 * SC                 # hip height standing on the cliff

# ---------------------------------------------------------------- timeline
T_RUN0, T_JUMP = 1.0, 1.9
J_VX, J_VY, J_G = 220.0, -700.0, 1800.0
J_X0 = 372.0
T_SPLASH1 = None
T_UP1_0, T_UP1_1 = 3.6, 4.6             # climbs back up
T_W2_0, T_W2_1 = 4.8, 5.3               # walks to the planks
T_PICK = 5.6
T_CARRY1 = 6.15
T_SLIDE1 = 6.6                          # the plank is out (too short)
T_STEP1 = 7.0
T_TIP1 = 7.4
T_SPLASH2 = 8.35
T_UP2_0, T_UP2_1 = 8.6, 9.6
T_SIT0, T_SIT1 = 9.6, 10.0              # sits down to think
T_Q0, T_BULB, T_BULB1 = 10.15, 10.9, 11.6
T_W3_0, T_W3_1 = 11.5, 11.85
T_TIE0, T_TIE1 = 11.9, 12.8
T_PUSH0, T_PUSH1 = 12.8, 13.6           # the long plank lands on the far cliff
T_CROSS0, T_CROSS1 = 13.75, 15.0
T_OPEN = 15.25
T_LUCKY = 16.0
T_L1, T_L2 = 17.2, 18.6
CPS = 16.0
LINE1, LINE2 = "HE CALLED IT LUCK.", "IT WAS TRY NUMBER 3."
TRIES = [(T_JUMP, 1), (T_SLIDE1, 2), (T_PUSH0, 3)]
T_PHONE = 8.4

BUB_OT = [(0.35, 2.0, "TOO FAR."), (3.5, 5.0, "TOLD YOU."), (8.7, 10.3, "JUST GIVE UP."), (T_LUCKY, 17.6, "LUCKY.")]


def tries(t):
    n = 0
    for t0, k in TRIES:
        if t >= t0:
            n = k
    return n


def jump_pos(tau):
    return J_X0 + J_VX * tau, STAND_Y + J_VY * tau + 0.5 * J_G * tau * tau


def _splash1():
    tau = 0.0
    while True:
        tau += 1 / 600
        x, y = jump_pos(tau)
        if y > RIVER - 30:
            return T_JUMP + tau, x


T_SPLASH1, X_SPLASH1 = _splash1()

# ---------------------------------------------------------------- poses (facing right, from the hip, unscaled)
STAND = PW.STAND
CROUCH = {"head": (34, -108), "neck": (24, -70), "el": (44, -30), "hl": (74, 8), "er": (40, -26), "hr": (70, 12),
          "kl": (34, 18), "fl": (4, 66), "kr": (44, 26), "fr": (62, 68)}
JUMP = {"head": (18, -146), "neck": (12, -104), "el": (-14, -142), "hl": (-22, -188), "er": (34, -140),
        "hr": (46, -186), "kl": (34, 26), "fl": (6, 70), "kr": (40, 22), "fr": (14, 74)}
FALL = {"head": (0, -150), "neck": (0, -108), "el": (-40, -146), "hl": (-58, -192), "er": (40, -146), "hr": (58, -192),
        "kl": (-12, 56), "fl": (-22, 112), "kr": (14, 54), "fr": (30, 108)}
HANG = {"head": (4, -150), "neck": (2, -108), "el": (22, -150), "hl": (34, -196), "er": (30, -150), "hr": (42, -192),
        "kl": (-4, 56), "fl": (-6, 113), "kr": (6, 56), "fr": (8, 113)}
THINK = {"head": (8, -150), "neck": (2, -108), "el": (30, -60), "hl": (52, -30), "er": (30, -70), "hr": (20, -118),
         "kl": (62, -26), "fl": (92, 28), "kr": (56, -20), "fr": (86, 32)}
CARRY = dict(STAND, el=(30, -66), hl=(62, -62), er=(26, -62), hr=(58, -58))
PUSH = {"head": (54, -116), "neck": (40, -80), "el": (72, -58), "hl": (104, -48), "er": (68, -54), "hr": (100, -44),
        "kl": (22, 50), "fl": (-30, 96), "kr": (42, 40), "fr": (60, 96)}
BALANCE = dict(STAND, el=(-40, -96), hl=(-86, -100), er=(40, -96), hr=(86, -100))
CHEER = PW.ARMS_UP
OT_SIT = dict(AJ.SIT_TYPE, el=(30, -60), hl=(54, -14), er=(26, -56), hr=(50, -10))
OT_PHONE = dict(AJ.SIT_TYPE, head=(16, -140), neck=(10, -100), el=(24, -58), hl=(46, -76), er=(20, -54), hr=(42, -72))
OT_UP = dict(OT_PHONE, head=(8, -152), neck=(4, -108))


def walk(t, base, speed=7.0):
    return AJ.walk(t * speed, base)


def at_hip(pose, x, y, facing=1, ang=0.0):
    return AJ.place(pose, (x, y), facing, SC, ang)


def climb(t, t0, t1):
    """Hanging on the left cliff's face, then up and over the edge."""
    u = prog(t, t0, t1)
    if u < 0.35:
        k = 0.0
    else:
        k = smooth((u - 0.35) / 0.65)
    x = lerp(LE + 36, LE - 60, k)
    y = lerp(CT + 200, STAND_Y, k)
    return lerp_pose(HANG, STAND, k), x, y, -1 if k < 0.6 else 1


def doer(t):
    """(pose, hip x, hip y, facing, rotation, alpha, prop)"""
    if t < T_RUN0:
        k = smooth(prog(t, 0.55, T_RUN0))
        return lerp_pose(STAND, CROUCH, 0.5 * k), 250, STAND_Y + 20 * k, 1, 0.0, 1.0, None
    if t < T_JUMP:
        u = prog(t, T_RUN0, T_JUMP)
        x = lerp(250, J_X0, u)
        return PW.run(t * 16), x, STAND_Y - 6 * abs(math.sin(t * 16)), 1, 0.0, 1.0, None
    if t < T_SPLASH1 + 0.1:
        tau = t - T_JUMP
        x, y = jump_pos(tau)
        k = smooth(prog(tau, 0.35, 0.75))
        p = lerp_pose(JUMP, FALL, k)
        if k > 0.5:
            p = dict(p, hl=(p["hl"][0] - 10 * math.sin(t * 20), p["hl"][1]), hr=(p["hr"][0] + 10 * math.sin(t * 20), p["hr"][1]))
        return p, x, y, 1, 0.0, 1.0, None
    if t < T_UP1_0:
        return STAND, -500, 0, 1, 0, 0.0, None
    if t < T_UP1_1:
        p, x, y, f = climb(t, T_UP1_0, T_UP1_1)
        return p, x, y, f, 0.0, 1.0, "drip"
    if t < T_W2_1:
        u = prog(t, T_W2_0, T_W2_1)
        x = lerp(LE - 60, 236, smooth(u))
        return walk(t, STAND), x, STAND_Y, -1 if t >= T_W2_0 else 1, 0.0, 1.0, "drip"
    if t < T_PICK:
        k = math.sin(math.pi * prog(t, T_W2_1, T_PICK))
        return lerp_pose(STAND, CROUCH, k), 236, STAND_Y + 30 * k, -1, 0.0, 1.0, "plank_lift" if t > (T_W2_1 + T_PICK) / 2 else None
    if t < T_CARRY1:
        u = prog(t, T_PICK, T_CARRY1)
        x = lerp(236, LE - 50, smooth(u))
        return walk(t, CARRY), x, STAND_Y, 1, 0.0, 1.0, "plank_carry"
    if t < T_SLIDE1:
        k = smooth(prog(t, T_CARRY1, T_SLIDE1))
        return lerp_pose(CARRY, CROUCH, k), LE - 50, STAND_Y + 30 * k, 1, 0.0, 1.0, None
    if t < T_STEP1:
        k = smooth(prog(t, T_SLIDE1, T_SLIDE1 + 0.15))
        u = prog(t, T_SLIDE1 + 0.1, T_STEP1)
        x = lerp(LE - 50, LE + 80, smooth(u))
        return walk(t, BALANCE), x, STAND_Y - 10 * smooth(u), 1, 0.0, 1.0, None
    if t < T_SPLASH2 + 0.1:
        # the plank tips around the edge and he goes down with it
        u = prog(t, T_STEP1, T_TIP1)
        ang = 1.25 * in_quad(u)
        if t < T_TIP1:
            px, py = LE + 80 * math.cos(ang) + 0, CT - 10 + 80 * math.sin(ang)
            return lerp_pose(BALANCE, FALL, u), px + 4, py - 141 + 10, 1, ang * 0.5, 1.0, None
        tau = t - T_TIP1
        x = LE + 40 + 60 * tau
        y = CT + 40 + 260 * tau + 0.5 * J_G * tau * tau - 141
        p = dict(FALL, hl=(FALL["hl"][0] - 10 * math.sin(t * 20), FALL["hl"][1]))
        return p, x, y, 1, 0.6, 1.0, None
    if t < T_UP2_0:
        return STAND, -500, 0, 1, 0, 0.0, None
    if t < T_UP2_1:
        p, x, y, f = climb(t, T_UP2_0, T_UP2_1)
        return p, x, y, f, 0.0, 1.0, "drip"
    if t < T_SIT1:
        k = smooth(prog(t, T_SIT0, T_SIT1))
        return lerp_pose(STAND, THINK, k), LE - 60, lerp(STAND_Y, CT - 37, k), 1, 0.0, 1.0, None
    if t < T_W3_0:
        return THINK, LE - 60, CT - 37, 1, 0.0, 1.0, None
    if t < T_W3_1:
        k = smooth(prog(t, T_W3_0, T_W3_1))
        x = lerp(LE - 60, 240, k)
        return lerp_pose(THINK, CROUCH, k), x, lerp(CT - 37, STAND_Y + 30, k), 1, 0.0, 1.0, None
    if t < T_TIE1:
        p = dict(CROUCH)
        w = math.sin(t * 9)
        p["hl"] = (p["hl"][0] + 10 * w, p["hl"][1] - 6 * abs(w))
        p["hr"] = (p["hr"][0] - 8 * w, p["hr"][1] - 6 * abs(math.cos(t * 9)))
        return p, 240, STAND_Y + 30, 1, 0.0, 1.0, None
    if t < T_PUSH1:
        u = prog(t, T_PUSH0, T_PUSH1)
        x = lerp(240, LE - 70, smooth(u))
        return walk(t, PUSH, 6.0), x, STAND_Y + 18, 1, 0.0, 1.0, None
    if t < T_CROSS0:
        k = smooth(prog(t, T_PUSH1, T_CROSS0))
        return lerp_pose(PUSH, STAND, k), LE - 70, lerp(STAND_Y + 18, STAND_Y, k), 1, 0.0, 1.0, None
    if t < T_CROSS1:
        u = prog(t, T_CROSS0, T_CROSS1)
        x = lerp(LE - 70, CHEST_X - 120, smooth(u))
        sag = bridge_sag(x)
        return walk(t, BALANCE, 5.0), x, STAND_Y + sag, 1, 0.04 * math.sin(t * 5), 1.0, None
    if t < T_OPEN:
        k = smooth(prog(t, T_CROSS1, T_OPEN))
        return lerp_pose(STAND, CROUCH, 0.6 * k), CHEST_X - 120, STAND_Y + 18 * k, 1, 0.0, 1.0, None
    k = smooth(prog(t, T_OPEN + 0.2, T_OPEN + 0.6))
    return lerp_pose(lerp_pose(STAND, CROUCH, 0.6), CHEER, k), CHEST_X - 120, STAND_Y + 18 * (1 - k), 1, 0.0, 1.0, None


def bridge_sag(x):
    if x < LE or x > LE + 2 * PLANK_L:
        return 0.0
    return 14 * math.sin(math.pi * (x - LE) / (2 * PLANK_L))


def overthinker(t):
    hip = (ROCK_X + 20, CT - 144)
    if t < T_PHONE:
        return OT_SIT, hip, 1, None
    if T_LUCKY - 0.3 <= t < T_LUCKY + 1.6:
        k = smooth(prog(t, T_LUCKY - 0.3, T_LUCKY)) * (1 - smooth(prog(t, T_LUCKY + 1.2, T_LUCKY + 1.6)))
        return lerp_pose(OT_PHONE, OT_UP, k), hip, 1, "phone"
    k = smooth(prog(t, T_PHONE, T_PHONE + 0.4))
    return lerp_pose(OT_SIT, OT_PHONE, k), hip, 1, "phone" if k > 0.5 else None


# ---------------------------------------------------------------- the planks
def planks_on_ground(t):
    """How many planks lie in the stack on the left cliff."""
    if t < (T_W2_1 + T_PICK) / 2:
        return 3
    if t < T_TIE0:
        return 2
    return 0


def plank_poly(cx, cy, ang, L=PLANK_L, T=16):
    pts = [(-L / 2, -T / 2), (L / 2, -T / 2), (L / 2, T / 2), (-L / 2, T / 2)]
    return [(cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)) for x, y in pts]


def draw_plank(d, cx, cy, ang, L=PLANK_L, rope=False):
    ink = INK + (255,)
    poly = plank_poly(cx, cy, ang, L)
    d.polygon(poly, fill=(178, 128, 78, 255), outline=ink)
    d.line(poly + [poly[0]], fill=ink, width=3)
    for i in range(3):
        a = rot((-L / 2 + 20 + i * L / 3, -2), ang)
        b = rot((-L / 2 + 20 + i * L / 3 + L / 5, 2), ang)
        d.line([(cx + a[0], cy + a[1]), (cx + b[0], cy + b[1])], fill=(130, 88, 50, 255), width=2)
    if rope:
        for j in range(4):
            a = rot((-10 + j * 7, -12), ang)
            b = rot((-6 + j * 7, 12), ang)
            d.line([(cx + a[0], cy + a[1]), (cx + b[0], cy + b[1])], fill=(222, 196, 140, 255), width=4)


def draw_props(d, t, dp):
    """Planks, the rope and the long bridge."""
    # the stack
    n = planks_on_ground(t)
    for i in range(n):
        draw_plank(d, 200 + (i % 2) * 6, CT - 8 - i * 15, 0.0)
    # the rope coil
    if t < T_TIE0 + 0.3:
        for r in (18, 13, 8):
            d.ellipse([300 - r * 1.4, CT - 2 * r - 2, 300 + r * 1.4, CT - 2], outline=(222, 196, 140, 255), width=4)
    pose, x, y, f, rr, al, prop = dp
    # plank 1: lifted, carried, slid out, tipped, falling
    if prop == "plank_lift" or prop == "plank_carry" or (T_CARRY1 <= t < T_SPLASH2 + 0.2):
        if t < T_CARRY1:
            pts = at_hip(pose, x, y, f)
            hx = (pts["hl"][0] + pts["hr"][0]) / 2
            hy = (pts["hl"][1] + pts["hr"][1]) / 2
            draw_plank(d, hx + 30, hy + 2, 0.0)
        elif t < T_SLIDE1:
            u = smooth(prog(t, T_CARRY1, T_SLIDE1))
            draw_plank(d, lerp(LE - 30, LE + PLANK_L / 2 - 20, u), lerp(STAND_Y - 70, CT - 8, u), 0.0)
        elif t < T_STEP1:
            draw_plank(d, LE + PLANK_L / 2 - 20, CT - 8, 0.0)
        elif t < T_TIP1:
            ang = 1.25 * in_quad(prog(t, T_STEP1, T_TIP1))
            c = rot((PLANK_L / 2 - 20, -8), ang)
            draw_plank(d, LE + c[0], CT + c[1], ang)
        else:
            tau = t - T_TIP1
            cx = LE + 80 + 70 * tau
            cy = CT + 60 + 300 * tau + 0.5 * J_G * tau * tau
            if cy < RIVER:
                draw_plank(d, cx, cy, 1.25 + 2.2 * tau)
    # the long plank: two tied together, then pushed over the gap
    if t >= T_TIE0:
        k = smooth(prog(t, T_TIE0, T_TIE0 + 0.3))
        if t < T_PUSH0:
            x0 = lerp(140, 80, k)
        else:
            x0 = lerp(80, LE + 2 * PLANK_L - 2 * PLANK_L + 2 * PLANK_L - 2 * PLANK_L, 0) if False else \
                lerp(80, LE + 2 * PLANK_L - 2 * PLANK_L + (LE + 2 * PLANK_L + 10 - (LE + 2 * PLANK_L)), 0)
            u = smooth(prog(t, T_PUSH0, T_PUSH1))
            x0 = lerp(80, LE - 30, u)
        # the left end x0; the plank is 2L long
        L2 = 2 * PLANK_L
        tip = x0 + L2
        if t < T_PUSH1 and tip > LE:
            # the free end droops a little over the gap until it lands
            droop = 0.05 * smooth(clamp((tip - LE) / 300)) * (1 - smooth(prog(t, T_PUSH1 - 0.15, T_PUSH1)))
        else:
            droop = 0.0
        cx, cy = x0 + L2 / 2, CT - 8
        ang = droop
        if t >= T_PUSH1:
            # resting on both cliffs; a little sag under his feet
            sag_at = 0.0
            if T_CROSS0 <= t < T_CROSS1:
                u = prog(t, T_CROSS0, T_CROSS1)
                sag_at = bridge_sag(lerp(LE - 70, CHEST_X - 120, smooth(u)))
            left, right = (x0, CT - 8), (tip, CT - 8)
            mid = (cx, CT - 8 + sag_at)
            draw_plank(d, (left[0] + mid[0]) / 2, (left[1] + mid[1]) / 2, math.atan2(mid[1] - left[1], mid[0] - left[0]),
                       PLANK_L)
            draw_plank(d, (mid[0] + right[0]) / 2, (mid[1] + right[1]) / 2, math.atan2(right[1] - mid[1], right[0] - mid[0]),
                       PLANK_L)
            draw_plank(d, mid[0], mid[1], 0, 1, rope=True)
        else:
            a = rot((-PLANK_L / 2, 0), ang)
            b = rot((PLANK_L / 2, 0), ang)
            draw_plank(d, cx + a[0], cy + a[1], ang, PLANK_L)
            draw_plank(d, cx + b[0], cy + b[1] + PLANK_L * math.sin(ang) * 0.0, ang, PLANK_L)
            draw_plank(d, cx, cy, ang, 1, rope=t > T_TIE0 + 0.4)


def draw_chest(img, d, t):
    ink = INK + (255,)
    x0, x1 = CHEST_X - 58, CHEST_X + 58
    y1 = CT
    y0 = CT - 58
    opened = smooth(prog(t, T_OPEN, T_OPEN + 0.35))
    # the glow: a pulse before, a burst of light after
    gl = Image.new("RGBA", (520, 520), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl)
    pulse = 0.55 + 0.15 * math.sin(t * 3)
    r = 110 + 120 * opened
    gd.ellipse([260 - r, 260 - r, 260 + r, 260 + r], fill=GOLD + (int(120 * pulse + 110 * opened),))
    gl = gl.filter(ImageFilter.GaussianBlur(50))
    img.alpha_composite(gl, (int(CHEST_X - 260), int(CT - 40 - 260)))
    if opened > 0.01:
        rays = Image.new("RGBA", (W, 900), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rays)
        cx, cy = CHEST_X, 860
        for i in range(9):
            a = -math.pi / 2 + (i - 4) * 0.17 + 0.03 * math.sin(t * 2 + i)
            L = 700 * opened
            w = 0.05
            rd.polygon([(cx, cy), (cx + L * math.cos(a - w), cy + L * math.sin(a - w)),
                        (cx + L * math.cos(a + w), cy + L * math.sin(a + w))], fill=GOLD + (int(60 * opened),))
        rays = rays.filter(ImageFilter.GaussianBlur(10))
        img.alpha_composite(rays, (0, int(CT - 50 - 860)))
        d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x1, y1], 6, fill=(150, 92, 44, 255), outline=ink, width=4)
    d.rectangle([x0 + 4, y0 + 20, x1 - 4, y0 + 30], fill=GOLD + (255,))
    d.rectangle([CHEST_X - 9, y0 + 14, CHEST_X + 9, y0 + 36], fill=(255, 226, 120, 255), outline=ink, width=2)
    # the lid, hinged at the back
    hx, hy = x1, y0
    ang = -1.9 * opened
    lid = [(0, 0), (-116, 0), (-116, -30), (-10, -34)]
    pts = [(hx + px * math.cos(ang) - py * math.sin(ang), hy + px * math.sin(ang) + py * math.cos(ang)) for px, py in lid]
    d.polygon(pts, fill=(170, 106, 52, 255), outline=ink)
    d.line(pts + [pts[0]], fill=ink, width=4)
    if opened > 0.2:
        d.ellipse([x0 + 10, y0 - 12, x1 - 10, y0 + 12], fill=(255, 214, 90, 255), outline=ink, width=2)
        rng = np.random.default_rng(int(t * 10))
        for i in range(10):
            sx = CHEST_X + rng.uniform(-60, 60)
            sy = y0 - rng.uniform(10, 120) * opened
            s = rng.uniform(3, 7)
            d.line([(sx - s, sy), (sx + s, sy)], fill=(255, 250, 220, 220), width=2)
            d.line([(sx, sy - s), (sx, sy + s)], fill=(255, 250, 220, 220), width=2)
    return d


def draw_rock(d):
    ink = INK + (255,)
    pts = [(ROCK_X - 70, CT), (ROCK_X - 64, CT - 92), (ROCK_X - 30, CT - 128), (ROCK_X + 30, CT - 132),
           (ROCK_X + 66, CT - 96), (ROCK_X + 74, CT)]
    d.polygon(pts, fill=(70, 72, 86, 255), outline=ink)
    d.line(pts, fill=ink, width=4)
    d.line([(ROCK_X - 50, CT - 100), (ROCK_X + 40, CT - 118)], fill=(110, 114, 132, 255), width=3)


def thought(img, d, t, head):
    if not (T_Q0 <= t < T_BULB1):
        return
    hx, hy = head
    bx, by = hx + 90, hy - 150
    sc = out_back(prog(t, T_Q0, T_Q0 + 0.2))
    al = 1 - smooth(prog(t, T_BULB1 - 0.2, T_BULB1))
    if sc < 0.05:
        return
    a = int(255 * al)
    for r, ox, oy in ((7, 34, 92), (11, 54, 62)):
        d.ellipse([hx + ox - r, hy - oy - r, hx + ox + r, hy - oy + r], fill=(242, 240, 234, a), outline=INK + (a,), width=3)
    R = 58 * sc
    d.ellipse([bx - R, by - R, bx + R, by + R], fill=(242, 240, 234, a), outline=INK + (a,), width=4)
    if t < T_BULB:
        spaced(d, bx, by - 36 * sc, "?", font("InterDisplay-Bold.otf", int(64 * sc)), INK + (a,), 0)
    else:
        k = out_back(prog(t, T_BULB, T_BULB + 0.2))
        g = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([40, 40, 200, 200], fill=(255, 230, 120, int(160 * al)))
        g = g.filter(ImageFilter.GaussianBlur(26))
        img.alpha_composite(g, (int(bx - 120), int(by - 128)))
        d = ImageDraw.Draw(img)
        d.ellipse([bx - R, by - R, bx + R, by + R], fill=(242, 240, 234, a), outline=INK + (a,), width=4)
        r = 24 * k
        d.ellipse([bx - r, by - r - 10, bx + r, by + r - 10], fill=(255, 220, 90, a), outline=INK + (a,), width=4)
        d.rectangle([bx - 11 * k, by + r - 12, bx + 11 * k, by + r + 6], fill=(150, 150, 160, a), outline=INK + (a,), width=3)
        for i in range(6):
            ang = -math.pi / 2 + (i - 2.5) * 0.45
            d.line([(bx + 34 * k * math.cos(ang), by - 10 + 34 * k * math.sin(ang)),
                    (bx + 46 * k * math.cos(ang), by - 10 + 46 * k * math.sin(ang))], fill=(255, 200, 60, a), width=4)


def splash(d, t, t0, x):
    tau = t - t0
    if tau < 0 or tau > 1.0:
        return
    rng = np.random.default_rng(int(t0 * 100))
    for i in range(28):
        a = math.pi * (1.1 + rng.uniform(0, 0.8))
        v = rng.uniform(250, 620)
        px = x + math.cos(a) * v * tau
        py = RIVER + math.sin(a) * v * tau + 0.5 * 1600 * tau * tau
        if py > RIVER + 4:
            continue
        r = rng.uniform(2, 5)
        al = int(230 * (1 - tau))
        d.ellipse([px - r, py - r, px + r, py + r], fill=(210, 230, 255, al))
    rr = 30 + 120 * tau
    d.ellipse([x - rr, RIVER - rr * 0.18, x + rr, RIVER + rr * 0.18], outline=(200, 220, 250, int(200 * (1 - tau))),
              width=3)


def drips(d, t, pts):
    hx, hy = pts["head"]
    for i in range(3):
        ph = (t * 1.3 + i * 0.33) % 1.0
        x = hx - 30 + i * 30
        y = hy + 10 + 120 * ph
        a = int(200 * (1 - ph))
        d.ellipse([x - 4, y - 4, x + 4, y + 6], fill=(160, 200, 255, a))


# ---------------------------------------------------------------- the static night
def build_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.clip(yy / 1300, 0, 1)[..., None]
    img = (1 - g) * np.array([6, 8, 18], np.float32) + g * np.array([26, 32, 58], np.float32)
    d_m = np.sqrt((xx - 820) ** 2 + (yy - 700) ** 2)
    img += (np.exp(-(d_m / 260) ** 2) * 0.5)[..., None] * np.array([60, 70, 100], np.float32)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(5)
    for _ in range(200):
        x, y = rng.uniform(0, W), rng.uniform(0, 1050)
        b = int(rng.uniform(70, 220))
        r = rng.choice([0.8, 1.2, 1.8], p=[0.6, 0.3, 0.1])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, min(255, b + 20), 255))
    d.ellipse([820 - 44, 700 - 44, 820 + 44, 700 + 44], fill=(232, 230, 214, 255))
    # far mountains, two layers
    for base, amp, col, seed in ((1110, 150, (16, 20, 38), 1), (1150, 90, (22, 26, 46), 2)):
        r2 = np.random.default_rng(seed)
        pts = [(0, H)]
        x = 0
        while x <= W + 60:
            pts.append((x, base - amp * r2.uniform(0.3, 1.0)))
            x += r2.uniform(80, 160)
        pts.append((W, H))
        d.polygon(pts, fill=col + (255,))
    # the chasm: dark down to the river, a little mist above the water
    a = np.asarray(im).astype(np.float32)
    ch = (xx > LE - 2) & (xx < RE + 2) & (yy > CT)
    depth = np.clip((yy - CT) / (RIVER - CT), 0, 1)
    chc = (1 - depth)[..., None] * np.array([18, 20, 34], np.float32) + depth[..., None] * np.array([8, 9, 16], np.float32)
    mist = np.exp(-((yy - (RIVER - 60)) / 50) ** 2)[..., None] * np.array([40, 46, 66], np.float32)
    a[..., :3] = np.where(ch[..., None], chc + mist, a[..., :3])
    im = Image.fromarray(a.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([LE, RIVER, RE, H], fill=(20, 32, 58, 255))
    for i in range(14):
        x = LE + 20 + rng.uniform(0, RE - LE - 60)
        y = RIVER + 10 + rng.uniform(0, 100)
        d.line([(x, y), (x + rng.uniform(10, 30), y)], fill=(120, 150, 200, 255), width=2)
    # the cliffs
    ink = INK + (255,)
    for poly in ([(-10, CT), (LE, CT), (LE - 6, CT + 160), (LE + 10, CT + 320), (LE - 14, CT + 520), (LE + 6, H + 10),
                  (-10, H + 10)],
                 [(RE, CT), (W + 10, CT), (W + 10, H + 10), (RE - 8, H + 10), (RE + 12, CT + 430), (RE - 6, CT + 260),
                  (RE + 8, CT + 120)]):
        d.polygon(poly, fill=(38, 38, 50, 255), outline=ink)
        d.line(poly, fill=ink, width=5)
    d.line([(0, CT), (LE, CT)], fill=(104, 110, 136, 255), width=4)
    d.line([(RE, CT), (W, CT)], fill=(104, 110, 136, 255), width=4)
    for i in range(40):
        side = rng.uniform() < 0.5
        x = rng.uniform(10, LE - 30) if side else rng.uniform(RE + 30, W - 10)
        y = rng.uniform(CT + 40, H - 20)
        d.line([(x, y), (x + rng.uniform(10, 40), y + rng.uniform(-6, 6))], fill=(52, 52, 66, 255), width=3)
    draw_rock(d)
    return im


BG = None
FRAME0 = None


def sprite(pts, body, far, facing, rotate=0.0, glow=True, prop=None, t=0.0):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 110))
    AJ.draw_stick(cv, pts, body, far, facing)
    if prop == "phone":
        hx = (pts["hl"][0] + pts["hr"][0]) / 2
        hy = (pts["hl"][1] + pts["hr"][1]) / 2
        q0, q1 = cv.P((hx - 12, hy - 34)), cv.P((hx + 12, hy + 4))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 4 * AJ.SS, fill=(30, 34, 48, 255), outline=INK + (255,),
                               width=3 * AJ.SS)
        s0, s1 = cv.P((hx - 8, hy - 30)), cv.P((hx + 8, hy))
        cv.d.rectangle([s0[0], s0[1], s1[0], s1[1]], fill=(120, 190, 255, 255))
        for hn in ("hl", "hr"):
            AJ.disc(cv, pts[hn], 11 * SC + 6 * SC, INK + (255,))
            AJ.disc(cv, pts[hn], 11 * SC, body + (255,))
    return cv.done()


def frame(t):
    img = BG.copy()
    d = ImageDraw.Draw(img)
    d = draw_chest(img, d, t)
    dp = doer(t)
    draw_props(d, t, dp)
    # the overthinker
    pose, hip, f, prop = overthinker(t)
    pts_o = at_hip(pose, hip[0], hip[1], f)
    spr, off = sprite(pts_o, OT, OT_FAR, f, prop=prop)
    img.alpha_composite(spr, off)
    # the doer
    pose, x, y, f, rr, al, prop = dp
    pts_d = None
    if al > 0.01:
        pts_d = at_hip(pose, x, y, f, rr)
        spr, off = sprite(pts_d, DOER, DOER_FAR, f)
        gcol = (255, 214, 120) if t >= T_OPEN else (210, 228, 255)
        img.alpha_composite(PW.glow_of(spr, 0.6 + 0.6 * smooth(prog(t, T_OPEN, T_OPEN + 0.4)), 14, gcol), off)
        img.alpha_composite(spr, off)
    d = ImageDraw.Draw(img)
    # in try 2 the plank is drawn again over his feet while it tips
    if T_STEP1 <= t < T_TIP1:
        ang = 1.25 * in_quad(prog(t, T_STEP1, T_TIP1))
        c = rot((PLANK_L / 2 - 20, -8), ang)
        draw_plank(d, LE + c[0], CT + c[1], ang)
    if prop == "drip" and pts_d:
        drips(d, t, pts_d)
    splash(d, t, T_SPLASH1, X_SPLASH1)
    splash(d, t, T_SPLASH2, LE + 120)
    if pts_d is not None and T_Q0 <= t < T_BULB1:
        thought(img, d, t, pts_d["head"])
        d = ImageDraw.Draw(img)
    # the overthinker's lines
    for b0, b1, s in BUB_OT:
        if b0 <= t < b1:
            bs = AJ.bubble(s)
            sc = out_back(prog(t, b0, b0 + 0.18))
            a = 1 - smooth(prog(t, b1 - 0.12, b1))
            if sc < 0.05:
                continue
            spr2 = bs.resize((max(1, int(bs.width * sc)), max(1, int(bs.height * sc))), Image.LANCZOS)
            if a < 0.999:
                spr2.putalpha(spr2.split()[3].point(lambda v: int(v * a)))
            hx, hy = pts_o["head"]
            img.alpha_composite(spr2, (int(clamp(hx - 40, 16, W - 16 - spr2.width)), int(hy - 56 - spr2.height)))
    d = ImageDraw.Draw(img)
    # TRIES 0 : n
    spaced(d, W / 2, 168, "TRIES", font("Inter-SemiBold.otf", 28), (140, 148, 166, 255), 10)
    n = tries(t)
    ch = max([t0 for t0, k in TRIES if t0 <= t], default=-9)
    pop = math.exp(-(t - ch) * 8) if ch > 0 else 0.0
    spaced(d, 330, 212, "0", font("InterDisplay-Bold.otf", 118), (168, 172, 182, 255), 0)
    fN = font("InterDisplay-Bold.otf", int(118 * (1 + 0.22 * pop)))
    spaced(d, 750, 212 - 12 * pop, str(n), fN, PW.lerp_c((250, 250, 252), GOLD, pop) + (255,), 0)
    spaced(d, 330, 354, "OVERTHINKER", font("Inter-SemiBold.otf", 30), (150, 154, 166, 255), 7)
    spaced(d, 750, 354, "DOER", font("Inter-SemiBold.otf", 30), (240, 242, 248, 255), 7)
    fm = font(MONO, 50)
    for t0, s, y, col in ((T_L1, LINE1, 446, (250, 250, 252)), (T_L2, LINE2, 512, GOLD)):
        if t < t0:
            continue
        k = int(clamp((t - t0) * CPS, 0, len(s)))
        full = sum(fm.getlength(c) for c in s) + 3 * (len(s) - 1)
        xx = W / 2 - full / 2
        for c in s[:k]:
            d.text((xx, y), c, font=fm, fill=col + (255,))
            xx += fm.getlength(c) + 3
        if (k < len(s) or (s == LINE2 and t < t0 + len(s) / CPS + 1.0)) and int(t * 3.4) % 2 == 0:
            d.rectangle([xx + 2, y + 6, xx + 26, y + 56], fill=col + (220,))
    return np.asarray(img.convert("RGB"))


def init_worker():
    global BG
    BG = build_bg()


def render(i):
    global FRAME0
    t = i / FPS
    fr = frame(t)
    if t > DUR - XFADE:
        if FRAME0 is None:
            FRAME0 = frame(0.0).astype(np.float32)
        k = smooth(prog(t, DUR - XFADE, DUR))
        fr = (fr.astype(np.float32) * (1 - k) + FRAME0 * k).astype(np.uint8)
    return fr.tobytes()


# ---------------------------------------------------------------- sound (calm)
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    chords = [[50, 53, 57, 60], [46, 50, 53, 57], [48, 52, 55, 59], [45, 48, 52, 55]]
    roots = [38, 34, 36, 33]
    mel = [69, 67, 65, 64, 65, 67, 69, 72]
    for b in range(int(round(DUR / BAR))):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        for k, m in enumerate(ch):
            mix_in(mus, GS.pad(midi(m), BAR, 0.8, 1.4), t0, 0.045, (k - 1.5) * 0.4)
        mix_in(mus, GS.pad(midi(rt - 12), BAR, 0.3, 1.0), t0, 0.11)
        for q in (0, 2):
            mix_in(mus, GS.keys(midi(mel[(b * 2 + q // 2) % len(mel)])), t0 + q * BEAT + 0.05, 0.045, 0.25)
    mix_in(fx, noise(DUR, 3, lo=80, hi=600), 0, 0.015)                     # wind
    # footsteps while running and walking
    for ts in np.arange(T_RUN0, T_JUMP, 0.2):
        mix_in(fx, noise(0.05, int(ts * 100), lo=200, hi=1500) * env(int(0.05 * SR), 0.001, 0.015), ts, 0.07)
    # the jump: a whoosh; the falls: a long whoosh down; the splashes
    mix_in(fx, noise(0.5, 11, lo=600, hi=3000) * env(int(0.5 * SR), 0.1, 0.15), T_JUMP, 0.06)
    for t0, t1 in ((T_JUMP + 0.4, T_SPLASH1), (T_TIP1, T_SPLASH2)):
        dd = t1 - t0
        tt = np.arange(int(dd * SR)) / SR
        mix_in(fx, noise(dd, int(t0 * 10), lo=300, hi=2500) * (tt / dd) ** 1.5, t0, 0.06)
    for t0 in (T_SPLASH1, T_SPLASH2):
        mix_in(fx, noise(0.8, int(t0 * 10) + 1, lo=200, hi=5000) * env(int(0.8 * SR), 0.005, 0.2), t0, 0.22)
    # the planks: a scrape, a creak, a knock on the far cliff
    mix_in(fx, noise(0.4, 21, lo=300, hi=2000) * env(int(0.4 * SR), 0.05, 0.12), T_CARRY1 + 0.1, 0.06)
    tt = np.arange(int(0.4 * SR)) / SR
    mix_in(fx, np.sin(2 * np.pi * np.cumsum(260 - 120 * tt + 15 * np.sin(2 * np.pi * 11 * tt)) / SR) * np.clip(1 - tt / 0.4, 0, 1),
           T_STEP1 + 0.05, 0.03)
    mix_in(fx, noise(0.9, 22, lo=300, hi=2000) * env(int(0.9 * SR), 0.1, 0.3), T_PUSH0, 0.05)
    mix_in(fx, tone(140, 0.25, (1, 0.5), a=0.001, d=0.07), T_PUSH1, 0.2)
    mix_in(fx, noise(0.15, 23, lo=200, hi=1500) * env(int(0.15 * SR), 0.001, 0.04), T_PUSH1, 0.12)
    # the idea: a soft "ding"; the rope: little rubs
    for i, m in enumerate((84, 91)):
        mix_in(fx, GS.keys(midi(m), 1.2), T_BULB + i * 0.08, 0.07)
    for ts in np.arange(T_TIE0 + 0.1, T_TIE1, 0.22):
        mix_in(fx, noise(0.12, int(ts * 100), lo=1500, hi=5000) * env(int(0.12 * SR), 0.02, 0.04), ts, 0.03)
    # the chest: a creak, then a warm shimmer
    mix_in(fx, tone(180, 0.35, (1, 0.4), a=0.05, d=0.15, sweep=120), T_OPEN, 0.05)
    for i, m in enumerate((72, 76, 79, 84, 88, 91)):
        mix_in(fx, GS.keys(midi(m), 1.6), T_OPEN + 0.2 + i * 0.07, 0.06, -0.2 + i * 0.08)
    # the counter
    for t0, k in TRIES:
        mix_in(fx, GS.keys(midi(79 + 2 * k), 0.6), t0, 0.04)
    for b0, b1, s in BUB_OT:
        mix_in(fx, tone(700, 0.08, (1,), a=0.003, d=0.03), b0, 0.03)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i + int(t0), lo=1200, hi=4000) * env(int(0.03 * SR), 0.001, 0.008),
                       t0 + i / CPS, 0.05)
    x = mus + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "the-gap.mp4"
    only = os.environ.get("ONLY_FRAMES")
    if only:
        init_worker()
        os.makedirs(out, exist_ok=True)
        for s in only.split(","):
            t = float(s)
            Image.fromarray(np.frombuffer(render(int(round(t * FPS))), np.uint8).reshape(H, W, 3)).save(
                os.path.join(out, f"f{t:05.2f}.png"))
        return
    wav = out + ".wav"
    write_wav(wav, audio())
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init_worker) as pool:
        for i, b in enumerate(pool.imap(render, range(NF), chunksize=4)):
            p.stdin.write(b)
            if i % 120 == 0:
                print(f"{i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)


if __name__ == "__main__":
    main()
