#!/usr/bin/env python3
"""High-quality neon toolkit: every panel is drawn at 2x and downsampled (smooth lines), all neon strokes go to one
layer that gets one glow pass, plus a frame-wide bloom, camera push/shake and particles.

Coordinates passed to the helpers are in 1x panel units; the canvases are K times larger.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import perfect_wave as PW
import five_minutes as FM
from perfect_wave import font, clamp, lerp

K = 2
BOLD = FM.BOLD
CHARS = [("THE DOER", (245, 245, 255)), ("THE OVERTHINKER", (60, 220, 255)), ("THE QUITTER", (255, 150, 40)),
         ("THE SHOW-OFF", (255, 70, 200))]


def sc(p):
    return [(x * K, y * K) for x, y in p]


class Panel:
    """Three layers at 2x: solid (fills, text), neon (strokes that glow), fx (particles)."""

    def __init__(self, bg2x):
        self.bg = bg2x
        self.w, self.h = bg2x.size
        self.solid = Image.new("RGBA", bg2x.size, (0, 0, 0, 0))
        self.neon = Image.new("RGBA", bg2x.size, (0, 0, 0, 0))
        self.ds = ImageDraw.Draw(self.solid)
        self.dn = ImageDraw.Draw(self.neon)

    # --- neon strokes
    def line(self, pts, col, w=4, a=255, closed=False):
        p = sc(pts) + (sc([pts[0]]) if closed else [])
        self.dn.line(p, fill=col + (int(a),), width=int(w * K), joint="curve")
        for x, y in p:
            r = w * K / 2
            self.dn.ellipse([x - r, y - r, x + r, y + r], fill=col + (int(a),))

    def rect(self, box, col, w=4, a=255, r=0):
        x0, y0, x1, y1 = box
        self.dn.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], int(r * K), outline=col + (int(a),),
                                  width=int(w * K))

    def circle(self, cx, cy, r, col, w=4, a=255, fill=False):
        b = [(cx - r) * K, (cy - r) * K, (cx + r) * K, (cy + r) * K]
        if fill:
            self.dn.ellipse(b, fill=col + (int(a),))
        else:
            self.dn.ellipse(b, outline=col + (int(a),), width=int(w * K))

    # --- solids
    def fill_poly(self, pts, col, a=255):
        self.ds.polygon(sc(pts), fill=col + (int(a),))

    def fill_rect(self, box, col, a=255, r=0):
        x0, y0, x1, y1 = box
        self.ds.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], int(r * K), fill=col + (int(a),))

    def text(self, xy, s, size, col, a=255, center=True, spacing=2, neon=False):
        f = font(BOLD, int(size * K))
        d = self.dn if neon else self.ds
        x, y = xy
        if center:
            tw = sum(f.getlength(c) for c in s) + spacing * K * (len(s) - 1)
            x = x * K - tw / 2
        else:
            x = x * K
        for c in s:
            d.text((x, y * K), c, font=f, fill=col + (int(a),))
            x += f.getlength(c) + spacing * K

    def stick(self, pts, col, w=10, a=255):
        bones = [("neck", "hip"), ("neck", "el"), ("el", "hl"), ("neck", "er"), ("er", "hr"), ("hip", "kl"),
                 ("kl", "fl"), ("hip", "kr"), ("kr", "fr")]
        for b0, b1 in bones:
            self.line([pts[b0], pts[b1]], col, w, a)
        hx, hy = pts["head"]
        self.circle(hx, hy, w * 2.5, col, a=a, fill=True)

    def compose(self, glow=1.0):
        out = self.bg.copy()
        out.alpha_composite(self.solid)
        g = self.neon.filter(ImageFilter.GaussianBlur(9 * K))
        g.putalpha(g.split()[3].point(lambda v: int(min(255, v * 1.9 * glow))))
        g2 = self.neon.filter(ImageFilter.GaussianBlur(3 * K))
        out.alpha_composite(g)
        out.alpha_composite(g2)
        out.alpha_composite(self.neon)
        # white-hot core on the strokes
        core = self.neon.point(lambda v: v)
        r, gch, b, a = core.split()
        a = a.point(lambda v: int(v * 0.35))
        white = Image.new("RGBA", core.size, (255, 255, 255, 0))
        white.putalpha(a.filter(ImageFilter.MinFilter(3)))
        out.alpha_composite(white)
        return out


def night_bg(w, h, seed=0, floor_y=None):
    """2x background: deep night gradient, stars, a far neon skyline, a floor with a soft reflection, vignette."""
    rng = np.random.default_rng(seed)
    W2, H2 = w * K, h * K
    yy, xx = np.mgrid[0:H2, 0:W2].astype(np.float32)
    fy = (floor_y or h - 70) * K
    top = np.array([6, 6, 16], np.float32)
    mid = np.array([22, 14, 40], np.float32)
    k = np.clip(yy / fy, 0, 1)[..., None]
    img = top * (1 - k) + mid * k
    img = np.where((yy > fy)[..., None], np.array([10, 9, 18]) + (yy - fy)[..., None] * 0.0, img)
    img += rng.normal(0, 1.6, img.shape)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    for _ in range(70):
        x, y = rng.uniform(0, W2), rng.uniform(0, fy * 0.6)
        r = rng.uniform(0.8, 2.2)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 220, 255, int(rng.uniform(60, 200))))
    # far skyline
    x = 0
    sky = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sky)
    while x < W2:
        bw = rng.uniform(40, 110) * K
        bh = rng.uniform(40, 150) * K
        sd.rectangle([x, fy - bh, x + bw - 6, fy], fill=(18, 14, 34, 255))
        for wy in np.arange(fy - bh + 10 * K, fy - 8 * K, 16 * K):
            for wx in np.arange(x + 8 * K, x + bw - 14 * K, 14 * K):
                if rng.uniform() < 0.22:
                    c = [(255, 200, 120), (120, 200, 255), (255, 120, 200)][int(rng.integers(3))]
                    sd.rectangle([wx, wy, wx + 5 * K, wy + 7 * K], fill=c + (int(rng.uniform(60, 150)),))
        x += bw
    im.alpha_composite(sky)
    d.line([(0, fy), (W2, fy)], fill=(70, 60, 110, 255), width=2 * K)
    r = np.sqrt(((xx - W2 / 2) / W2) ** 2 + ((yy - H2 / 2) / H2) ** 2)
    vig = (np.clip((r - 0.25) * 1.6, 0, 1) * 170).astype(np.uint8)
    v = Image.new("RGBA", im.size, (0, 0, 0, 255))
    v.putalpha(Image.fromarray(vig, "L"))
    im.alpha_composite(v)
    return im


def downsample(im2x, w, h):
    return im2x.resize((w, h), Image.LANCZOS)


def camera(im, z=1.0, dx=0.0, dy=0.0):
    """Zoom about the centre and shift (1x pixels)."""
    if z <= 1.0001 and abs(dx) < 0.01 and abs(dy) < 0.01:
        return im
    w, h = im.size
    cw, ch = w / z, h / z
    x0 = clamp((w - cw) / 2 - dx / z, 0, w - cw)
    y0 = clamp((h - ch) / 2 - dy / z, 0, h - ch)
    return im.resize((w, h), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


def shake(t, events, amp=10, dur=0.35):
    dx = dy = 0.0
    for t0 in events:
        if t0 <= t < t0 + dur:
            k = 1 - (t - t0) / dur
            dx += amp * k * math.sin((t - t0) * 90)
            dy += amp * 0.6 * k * math.cos((t - t0) * 77)
    return dx, dy


def bloom(rgb, strength=0.55, thr=150, radius=22):
    """Frame-wide bloom: blur the bright parts and add them back."""
    a = rgb.astype(np.float32)
    bright = np.clip(a - thr, 0, 255) * (255 / (255 - thr))
    b = Image.fromarray(bright.astype(np.uint8), "RGB").resize((rgb.shape[1] // 4, rgb.shape[0] // 4), Image.BILINEAR)
    b = b.filter(ImageFilter.GaussianBlur(radius / 4)).resize((rgb.shape[1], rgb.shape[0]), Image.BILINEAR)
    out = a + strength * np.asarray(b, np.float32)
    return np.clip(out, 0, 255).astype(np.uint8)


def dust(p, t, seed, n=26, col=(200, 200, 255)):
    rng = np.random.default_rng(seed)
    w, h = p.w / K, p.h / K
    for _ in range(n):
        x0, y0, sp, ph = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(4, 14), rng.uniform(0, 6.28)
        x = (x0 + t * sp) % w
        y = y0 + 8 * math.sin(t * 0.7 + ph)
        a = 40 + 60 * (0.5 + 0.5 * math.sin(t * 1.3 + ph))
        r = rng.uniform(0.8, 1.8)
        p.ds.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=col + (int(a),))


def confetti(p, t, t0, t1, x, y, seed, n=40):
    if not (t0 <= t < t1 + 1.5):
        return
    rng = np.random.default_rng(seed)
    cols = [(255, 205, 60), (255, 70, 200), (60, 220, 255), (255, 255, 255), (120, 240, 150)]
    for j in range(n):
        st = t0 + (t1 - t0) * rng.uniform()
        if t < st:
            continue
        u = t - st
        if u > 1.6:
            continue
        vx, vy = rng.uniform(-180, 180), rng.uniform(-320, -120)
        px, py = x + vx * u, y + vy * u + 420 * u * u
        ang = u * 8 + j
        c, s = math.cos(ang), math.sin(ang)
        pts = [(px + c * dx - s * dy, py + s * dx + c * dy) for dx, dy in ((-5, -3), (5, -3), (5, 3), (-5, 3))]
        p.ds.polygon(sc(pts), fill=cols[j % len(cols)] + (int(255 * (1 - u / 1.6)),))


def pop(t, t0, d=0.3):
    """0 -> overshoot -> 1."""
    u = clamp((t - t0) / d)
    if u <= 0:
        return 0.0
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)
