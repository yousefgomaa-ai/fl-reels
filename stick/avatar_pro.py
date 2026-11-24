#!/usr/bin/env python3
"""Three bolder avatar options (800x800, built for the circle crop and for 40 px):
  A  FORK  - a road splits in two under the red-scarf hero: one branch gold and lit, one grey fading into the dark
  B  HALO  - a huge gold moon behind the hero, the scarf blowing, hard rim light
  C  SPLIT - the circle cut in two: cold blue with a grey figure walking away, warm gold with the hero walking on

    python3 stick/avatar_pro.py stick/avatar
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import compare as C  # noqa
from compare import K, INK, place  # noqa

S = 800
STAND = PW.STAND
GOLD = (246, 196, 92)
SCARF = (214, 40, 48)


def grad_bg(top, bottom):
    yy = np.linspace(0, 1, S, dtype=np.float32)[:, None, None]
    a = np.array(top, np.float32) * (1 - yy) + np.array(bottom, np.float32) * yy
    a = np.repeat(a, S, axis=1)
    return a


def glow(a, cx, cy, r, col, k=1.0):
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))
    return a + g[..., None] * np.array(col, np.float32) * k


def stars(d, seed, n, ymax=S):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.uniform(0, S), rng.uniform(0, ymax)
        r = rng.uniform(0.6, 1.8)
        d.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=(225, 230, 255, int(rng.uniform(60, 210))))


def to_im(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").resize((S * K, S * K), Image.BICUBIC).convert("RGBA")


def scarf_flow(d, neck, s, t=0.0, f=-1):
    nx, ny = neck
    pts = [(nx, ny + 4 * s)]
    for j in range(1, 7):
        pts.append((nx + f * j * 16 * s, ny + 10 * s + 10 * s * math.sin(j * 0.9 + t) + j * 3 * s))
    for w, col in ((15 * s, INK), (11 * s, SCARF)):
        d.line([(x * K, y * K) for x, y in pts], fill=col + (255,), width=int(w * K), joint="curve")
    d.ellipse([(nx - 22 * s) * K, (ny - 8 * s) * K, (nx + 22 * s) * K, (ny + 14 * s) * K], fill=SCARF + (255,),
              outline=INK + (255,), width=int(2 * K))


def finish(im, name, out):
    im = im.resize((S, S), Image.LANCZOS).convert("RGB")
    im.save(os.path.join(out, name))
    return im


def option_fork(out):
    a = grad_bg((6, 7, 12), (14, 14, 20))
    a = glow(a, 560, 250, 260, (120, 84, 30))
    im = to_im(a)
    d = ImageDraw.Draw(im)
    stars(d, 1, 120, 420)
    fx, fy = 400, 560                      # the fork point
    # the two branches (perspective strips into the distance)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)

    def branch(x_far, y_far, col, w_near=90, w_far=16):
        n = 30
        left, right = [], []
        for j in range(n + 1):
            u = j / n
            x = fx + (x_far - fx) * (u ** 0.9) + (1 - u) * 0
            y = fy + (y_far - fy) * u
            w = w_near + (w_far - w_near) * u
            left.append((x - w / 2, y))
            right.append((x + w / 2, y))
        ld.polygon([(x * K, y * K) for x, y in left + right[::-1]], fill=col)
    branch(640, 330, (235, 186, 90, 255))
    branch(170, 360, (60, 62, 72, 255))
    ld.polygon([((fx - 150) * K, S * K), ((fx + 150) * K, S * K), ((fx + 45) * K, fy * K), ((fx - 45) * K, fy * K)],
               fill=(150, 130, 100, 255))
    lay = lay.filter(ImageFilter.GaussianBlur(1.5 * K))
    gl = lay.resize((S // 4, S // 4)).filter(ImageFilter.GaussianBlur(8)).resize(im.size)
    im.alpha_composite(gl)
    im.alpha_composite(lay)
    s = 1.55
    pose = dict(STAND, head=(0, -152), el=(-16, -60), hl=(-22, -14), er=(16, -60), hr=(22, -14))
    pts = place(pose, (fx, fy + 30 - 113 * s), 1, s)
    C.figure(im, pts, s, light=(0.6, -0.8))
    scarf_flow(ImageDraw.Draw(im), pts["neck"], s, 0.4, -1)
    return finish(im, "avatar-pro-A-fork.png", out)


def option_halo(out):
    a = grad_bg((5, 6, 10), (10, 10, 14))
    a = glow(a, 400, 330, 330, (110, 76, 24))
    im = to_im(a)
    d = ImageDraw.Draw(im)
    stars(d, 2, 140)
    # the moon
    mx, my, mr = 400, 330, 220
    d.ellipse([(mx - mr) * K, (my - mr) * K, (mx + mr) * K, (my + mr) * K], fill=(252, 214, 130, 255))
    for cx, cy, r in ((-70, -40, 34), (60, 50, 26), (-20, 90, 18), (90, -80, 16)):
        d.ellipse([(mx + cx - r) * K, (my + cy - r) * K, (mx + cx + r) * K, (my + cy + r) * K], fill=(236, 192, 108, 255))
    s = 2.1
    # walking, seen against the moon, scarf blowing
    pose = dict(STAND, head=(6, -152), neck=(3, -108), el=(-24, -64), hl=(-38, -22), er=(26, -64), hr=(42, -26),
                kl=(-22, 52), fl=(-34, 110), kr=(28, 50), fr=(40, 110))
    pts = place(pose, (400, 800 - 60 - 113 * s), 1, s)
    C.figure(im, pts, s, light=(0.0, -1.0))
    scarf_flow(ImageDraw.Draw(im), pts["neck"], s, 1.0, -1)
    d = ImageDraw.Draw(im)
    d.rectangle([0, (800 - 60) * K, S * K, S * K], fill=(12, 12, 16, 255))
    d.line([0, (800 - 60) * K, S * K, (800 - 60) * K], fill=(250, 210, 130, 200), width=3 * K)
    return finish(im, "avatar-pro-B-halo.png", out)


def option_split(out):
    left = grad_bg((10, 18, 34), (6, 10, 20))
    right = grad_bg((44, 30, 10), (16, 12, 8))
    xx = np.arange(S)[None, :, None]
    a = np.where(xx < S // 2, left, right)
    a = glow(a, 600, 360, 240, (120, 80, 20))
    a = glow(a, 200, 360, 240, (20, 40, 80))
    im = to_im(a)
    d = ImageDraw.Draw(im)
    stars(d, 3, 120)
    d.line([(S // 2) * K, 0, (S // 2) * K, S * K], fill=(255, 236, 190, 230), width=3 * K)
    floor = 640
    d.line([0, floor * K, (S // 2) * K, floor * K], fill=(60, 80, 120, 255), width=3 * K)
    d.line([(S // 2) * K, floor * K, S * K, floor * K], fill=GOLD + (255,), width=4 * K)
    s = 1.45
    gp = dict(C.SAD, kl=(-20, 52), fl=(-30, 110), kr=(20, 50), fr=(30, 112))
    gpts = place(gp, (230, floor - 113 * s), -1, s)
    C.figure(im, gpts, s, light=(0.6, -0.8), body=(110, 120, 140))
    hp = dict(STAND, head=(8, -152), neck=(4, -108), el=(-22, -64), hl=(-36, -24), er=(24, -64), hr=(40, -28),
              kl=(-22, 52), fl=(-34, 110), kr=(28, 50), fr=(40, 110))
    hpts = place(hp, (570, floor - 113 * s), 1, s)
    C.figure(im, hpts, s, light=(-0.6, -0.8))
    scarf_flow(ImageDraw.Draw(im), hpts["neck"], s, 0.6, -1)
    return finish(im, "avatar-pro-C-split.png", out)


def sheet(ims, out):
    """each option as a circle at 400, 120 and 40 px"""
    W = 3 * 420
    sh = Image.new("RGB", (W, 600), (24, 24, 28))
    d = ImageDraw.Draw(sh)
    for i, (im, lab) in enumerate(zip(ims, ("A  FORK", "B  HALO", "C  SPLIT"))):
        x0 = i * 420 + 10
        for size, (ox, oy) in ((400, (0, 0)), (120, (40, 430)), (40, (220, 470))):
            m = Image.new("L", (size, size), 0)
            ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
            sh.paste(im.resize((size, size), Image.LANCZOS), (x0 + ox, oy), m)
        d.text((x0 + 280, 440), lab, fill=(230, 230, 236))
    sh.save(os.path.join(out, "avatar-pro-compare.png"))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "avatar"
    os.makedirs(out, exist_ok=True)
    ims = [option_fork(out), option_halo(out), option_split(out)]
    sheet(ims, out)
    print("ok")


# ---------------------------------------------------------------- C, developed further
def scarf_tails(d, neck, s, f=-1):
    """a knot at the neck and two tapered tails blowing back in waves"""
    nx, ny = neck
    for k2, (amp, ph, ln, dy) in enumerate(((9, 0.0, 6, 0), (7, 1.4, 5, 12))):
        top, bot = [], []
        for j in range(ln + 1):
            u = j / ln
            x = nx + f * j * 13 * s
            y = ny + (6 + dy) * s + amp * s * math.sin(j * 0.85 + ph) * u + j * 2.5 * s
            w = (15 - 8 * u) * s
            top.append((x, y - w / 2))
            bot.append((x, y + w / 2))
        poly_pts = [(x * K, y * K) for x, y in top + bot[::-1]]
        d.polygon(poly_pts, fill=(176, 26, 36, 255) if k2 else SCARF + (255,), outline=INK + (255,), width=int(2 * K))
    d.ellipse([(nx - 24 * s) * K, (ny - 9 * s) * K, (nx + 24 * s) * K, (ny + 15 * s) * K], fill=SCARF + (255,),
              outline=INK + (255,), width=int(2 * K))
    d.ellipse([(nx - 10 * s) * K, (ny - 2 * s) * K, (nx + 4 * s) * K, (ny + 8 * s) * K], fill=(236, 90, 96, 255))


def tinted_glow(base, layer, col, a=0.6, blur=10):
    g = layer.resize((layer.width // 4, layer.height // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur))
    gl = Image.new("RGBA", g.size, col + (0,))
    gl.putalpha(g.split()[3].point(lambda v: int(v * a)))
    base.alpha_composite(gl.resize(layer.size, Image.BILINEAR))


def option_split_v2(out):
    floor = 650
    mid = S // 2
    left = grad_bg((12, 22, 44), (5, 8, 16))
    right = grad_bg((52, 34, 10), (14, 10, 6))
    xx = np.arange(S)[None, :, None]
    a = np.where(xx < mid, left, right)
    a = glow(a, 660, 300, 260, (150, 100, 26))
    a = glow(a, 150, 320, 240, (16, 40, 90))
    a = glow(a, mid, 380, 70, (120, 110, 90), 0.5)
    im = to_im(a)
    d = ImageDraw.Draw(im)
    stars(d, 3, 90, floor - 40)
    # light rays on the warm side
    rays = Image.new("RGBA", im.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    for j in range(5):
        x0 = mid + 120 + j * 70
        rd.polygon([(x0 * K, 0), ((x0 + 34) * K, 0), ((x0 - 60) * K, floor * K), ((x0 - 120) * K, floor * K)],
                   fill=(255, 210, 120, 22))
    rays = rays.filter(ImageFilter.GaussianBlur(10 * K))
    im.alpha_composite(rays)
    # floors: a wet cold half and a warm half
    d = ImageDraw.Draw(im)
    d.rectangle([0, floor * K, mid * K, S * K], fill=(8, 12, 24, 255))
    d.rectangle([mid * K, floor * K, S * K, S * K], fill=(22, 15, 8, 255))
    d.line([0, floor * K, mid * K, floor * K], fill=(70, 96, 150, 255), width=3 * K)
    d.line([mid * K, floor * K, S * K, floor * K], fill=GOLD + (255,), width=4 * K)
    # the figures on their own layer (for glows and reflections)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    s = 1.62
    gp = {"head": (-26, -134), "neck": (-16, -98), "el": (-8, -54), "hl": (6, -14), "er": (-30, -56), "hr": (-26, -12),
          "kl": (-26, 52), "fl": (-36, 112), "kr": (16, 52), "fr": (28, 110)}
    gpts = place(gp, (215, floor - 113 * s), -1, s)
    C.figure(lay, gpts, s, light=(-0.7, -0.7), body=(116, 126, 148))
    hp = dict(STAND, head=(10, -154), neck=(5, -109), el=(-28, -66), hl=(-44, -28), er=(30, -70), hr=(48, -34),
              kl=(-26, 52), fl=(-40, 110), kr=(30, 50), fr=(44, 110))
    hpts = place(hp, (585, floor - 113 * s), 1, s)
    C.figure(lay, hpts, s, light=(0.7, -0.7))
    scarf_tails(ImageDraw.Draw(lay), hpts["neck"], s, -1)
    left_l = lay.crop((0, 0, mid * K, S * K))
    right_l = lay.crop((mid * K, 0, S * K, S * K))
    tinted_glow(im, lay.crop((0, 0, mid * K, S * K)).resize(lay.size) if False else lay, (90, 140, 255), 0.0)
    gl_left = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gl_left.alpha_composite(left_l, (0, 0))
    gl_right = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gl_right.alpha_composite(right_l, (mid * K, 0))
    tinted_glow(im, gl_left, (90, 140, 255), 0.55)
    tinted_glow(im, gl_right, (255, 200, 110), 0.65)
    # reflections in the wet floor
    top = lay.crop((0, 0, S * K, floor * K))
    refl = top.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, S * K, (S - floor) * K))
    refl = refl.resize((refl.width // 4, refl.height // 4)).filter(ImageFilter.GaussianBlur(2)).resize(refl.size)
    fade = np.linspace(0.42, 0.0, refl.height, dtype=np.float32)[:, None]
    refl.putalpha(Image.fromarray((np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)))
    im.alpha_composite(refl, (0, floor * K))
    im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    # rain on the cold side, sparks on the warm side
    rng = np.random.default_rng(5)
    for _ in range(70):
        x, y = rng.uniform(0, mid - 6), rng.uniform(0, floor + 40)
        d.line([(x * K, y * K), ((x - 7) * K, (y + 28) * K)], fill=(150, 175, 220, 120), width=int(1.6 * K))
    for _ in range(40):
        x, y = rng.uniform(mid + 10, S), rng.uniform(80, floor - 10)
        r = rng.uniform(1.5, 3.8)
        d.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=(255, 222, 150, int(rng.uniform(120, 230))))
    # the seam: a soft bright line
    seam = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(seam)
    sd.line([(mid * K, 0), (mid * K, S * K)], fill=(255, 240, 210, 255), width=10 * K)
    im.alpha_composite(seam.filter(ImageFilter.GaussianBlur(9 * K)))
    d = ImageDraw.Draw(im)
    d.line([(mid * K, 0), (mid * K, S * K)], fill=(255, 246, 226, 255), width=2 * K)
    # vignette
    yy, xx2 = np.mgrid[0:S * K:4, 0:S * K:4].astype(np.float32) / K
    r = np.sqrt((xx2 - S / 2) ** 2 + (yy - S / 2) ** 2) / (S / 2)
    vig = Image.fromarray((np.clip((r - 0.75) * 2.2, 0, 1) * 200).astype(np.uint8)).resize(im.size)
    v = Image.new("RGBA", im.size, (0, 0, 0, 255))
    v.putalpha(vig)
    im.alpha_composite(v)
    return finish(im, "avatar-pro-C2-split.png", out)


def preview_one(im, out, name):
    sh = Image.new("RGB", (580, 420), (24, 24, 28))
    for size, (ox, oy) in ((400, (10, 10)), (120, (430, 20)), (40, (470, 170))):
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
        sh.paste(im.resize((size, size), Image.LANCZOS), (ox, oy), m)
    sh.save(os.path.join(out, name))
