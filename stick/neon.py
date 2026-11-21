#!/usr/bin/env python3
"""Neon 4-mind format: our own fixed characters with fixed neon colours, stacked panels, a question on top.

THE DOER (white), THE OVERTHINKER (cyan), THE QUITTER (orange), THE SHOW-OFF (pink).
Shared drawing helpers: glowing stick figures, panel frames, labels, bars, the title.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import perfect_wave as PW
import ai_job as AJ
import five_minutes as FM
from perfect_wave import font, spaced, clamp

BOLD = FM.BOLD
W, H = 1080, 1920
CHARS = [("THE DOER", (245, 245, 255)), ("THE OVERTHINKER", (60, 220, 255)), ("THE QUITTER", (255, 150, 40)),
         ("THE SHOW-OFF", (255, 70, 200))]
TITLE_H = 250
PANEL_H = 400
GAP = 12
PX0, PX1 = 24, W - 24


def panel_y(i):
    return TITLE_H + i * (PANEL_H + GAP)


def panel_bg(w, h, seed=0):
    """Dark textured wall (faint bricks), a floor, a soft vignette."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32) + np.array([12, 12, 18])
    # bricks
    by = (yy // 34).astype(int)
    off = (by % 2) * 40
    mortar = ((yy % 34) < 2) | (((xx + off) % 80) < 2)
    img = np.where(mortar[..., None], img + 7, img)
    img += rng.normal(0, 2.5, img.shape)
    floor = h - 70
    img = np.where((yy > floor)[..., None], np.array([16, 16, 22]) + rng.normal(0, 2, img.shape), img)
    r = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2)
    img *= (1 - 0.5 * np.clip(r - 0.2, 0, 1))[..., None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    ImageDraw.Draw(im).line([(0, floor), (w, floor)], fill=(40, 40, 52, 255), width=2)
    return im


def neon_stick(im, pts, col, width=9, glow=1.0, head_r=None):
    """A glowing neon stick figure: white-hot core, coloured line, wide soft glow."""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    bones = [("neck", "hip"), ("neck", "el"), ("el", "hl"), ("neck", "er"), ("er", "hr"), ("hip", "kl"), ("kl", "fl"),
             ("hip", "kr"), ("kr", "fr")]
    hr = head_r or width * 2.6
    hx, hy = pts["head"]
    for a, b in bones:
        d.line([pts[a], pts[b]], fill=col + (255,), width=width, joint="curve")
    for k in ("hl", "hr", "fl", "fr", "el", "er", "kl", "kr", "hip", "neck"):
        x, y = pts[k]
        d.ellipse([x - width / 2, y - width / 2, x + width / 2, y + width / 2], fill=col + (255,))
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=col + (255,))
    g = lay.filter(ImageFilter.GaussianBlur(width * 1.6))
    a = g.split()[3].point(lambda v: int(min(255, v * 1.6 * glow)))
    g.putalpha(a)
    im.alpha_composite(g)
    im.alpha_composite(lay)
    core = Image.new("RGBA", im.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    for a2, b2 in bones:
        cd.line([pts[a2], pts[b2]], fill=(255, 255, 255, 150), width=max(2, width // 3))
    im.alpha_composite(core)


def neon_line(im, pts, col, width=4, glow=1.0, closed=False):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    p = list(pts) + ([pts[0]] if closed else [])
    d.line(p, fill=col + (255,), width=width, joint="curve")
    g = lay.filter(ImageFilter.GaussianBlur(width * 2))
    g.putalpha(g.split()[3].point(lambda v: int(min(255, v * 1.4 * glow))))
    im.alpha_composite(g)
    im.alpha_composite(lay)


def neon_rect(im, box, col, width=4, glow=1.0, radius=0):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle(box, radius, outline=col + (255,), width=width)
    g = lay.filter(ImageFilter.GaussianBlur(width * 2))
    g.putalpha(g.split()[3].point(lambda v: int(min(255, v * 1.4 * glow))))
    im.alpha_composite(g)
    im.alpha_composite(lay)


def neon_text(im, xy, s, size, col, anchor_center=True, spacing=3, glow=1.0):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = font(BOLD, size)
    if anchor_center:
        spaced(d, xy[0], xy[1], s, f, col + (255,), spacing)
    else:
        d.text(xy, s, font=f, fill=col + (255,))
    g = lay.filter(ImageFilter.GaussianBlur(size / 6))
    g.putalpha(g.split()[3].point(lambda v: int(min(255, v * 1.5 * glow))))
    im.alpha_composite(g)
    im.alpha_composite(lay)


def label(im, i, extra=None):
    name, col = CHARS[i]
    d = ImageDraw.Draw(im)
    d.ellipse([18, 20, 32, 34], fill=col + (255,))
    d.text((42, 12), name, font=font(BOLD, 28), fill=col + (255,))


def bar(im, x, y, w, k, col, text):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + w, y + 12], 6, fill=(40, 40, 52, 255))
    if k > 0.005:
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).rounded_rectangle([x, y, x + max(12, w * clamp(k)), y + 12], 6, fill=col + (255,))
        g = lay.filter(ImageFilter.GaussianBlur(5))
        im.alpha_composite(g)
        im.alpha_composite(lay)
    ImageDraw.Draw(im).text((x, y - 34), text, font=font(BOLD, 24), fill=(200, 204, 214, 255))
