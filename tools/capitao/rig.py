"""Capitão Caveira — pixel-art rig.

Draws the boss frame by frame at 1:1 (no resize anywhere): limbs are flat-shaded capsules posed
with two-bone IK, the head is a hand-placed pixel template per phase. All three phases share one
skeleton, one palette and the same legs/boots/belt, so they read as the same man getting wrecked.

World coordinates: x forward (the sprite faces right), y up, origin = the anchor on the ground.
"""
from math import atan2, cos, sin, radians, hypot, acos, pi

import numpy as np
from PIL import Image, ImageDraw

F = 176          # frame size (square), as the game expects for zk* sheets
AX = 72          # anchor column
GY = 174         # ground row (feet stand on this row)


def hx(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# ramps: outline, dark, mid, light, highlight
RAMP = {
    "uni":   ["#0d0f15", "#1a1e28", "#29303f", "#3b4356", "#525c74"],
    "vest":  ["#121309", "#24281b", "#373d29", "#4f583b", "#69744d"],
    "gear":  ["#18120a", "#382c1c", "#55452e", "#75613e", "#927a4e"],
    "boot":  ["#09090b", "#151519", "#222228", "#32323a", "#44444e"],
    "glove": ["#0b0c0e", "#1c1e22", "#2c2f35", "#41454d", "#565b64"],
    "bone":  ["#2a2018", "#86795f", "#b5a98c", "#ddd3b6", "#f3edd8"],
    "skin":  ["#1a2016", "#45513c", "#617057", "#7f9174", "#9fb093"],
    "flesh": ["#16130f", "#36412c", "#526245", "#6f845c", "#90a577"],
    "rage":  ["#260b09", "#5c1d18", "#88302a", "#ae4a3b", "#cf6a52"],
    "metal": ["#0b0c0e", "#1b1d21", "#2b2e34", "#42464e", "#5e636c"],
    "blood": ["#2a0505", "#5e100e", "#901a16", "#bb2c22", "#d84a36"],
}
RAMP = {k: [hx(c) for c in v] for k, v in RAMP.items()}
EYE = hx("#ff3b26")
EYE_HOT = hx("#ffd2a0")
SOCKET = hx("#120a0a")
FLASH = [hx("#fff6c8"), hx("#ffd24a"), hx("#ff8a26")]
OUTLINE = {1: hx("#0c0b0f"), 2: hx("#0c0b0f"), 3: hx("#2a0606")}


# ---------------------------------------------------------------- geometry helpers
def V(x, y):
    return np.array([float(x), float(y)])


def rot(p, a):
    c, s = cos(a), sin(a)
    return V(p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def ang(deg):
    """Limb direction: 0 = straight down, +90 = forward, 180 = up."""
    r = radians(deg)
    return V(sin(r), -cos(r))


def ik(a, t, l1, l2, pick):
    """Two-bone IK from a to t. pick(j1, j2) chooses the joint (knee forward, elbow down...)."""
    d = t - a
    dist = hypot(*d)
    if dist < 1e-3:
        d, dist = V(0, -1), 1e-3
    dist_c = min(max(dist, abs(l1 - l2) + 0.01), l1 + l2 - 0.01)
    base = atan2(d[1], d[0])
    c = (l1 * l1 + dist_c * dist_c - l2 * l2) / (2 * l1 * dist_c)
    off = acos(max(-1, min(1, c)))
    j1 = a + l1 * V(cos(base + off), sin(base + off))
    j2 = a + l1 * V(cos(base - off), sin(base - off))
    j = pick(j1, j2)
    end = a + d / dist * dist_c if dist > l1 + l2 - 0.01 else t
    return j, end


def knee_fwd(j1, j2):
    return j1 if j1[0] >= j2[0] else j2


def elbow_down(j1, j2):
    return j1 if j1[1] <= j2[1] else j2


def elbow_back(j1, j2):
    return j1 if j1[0] <= j2[0] else j2


def elbow_up(j1, j2):
    return j1 if j1[1] >= j2[1] else j2


def circle(c, r, n=14):
    return [c + r * V(cos(2 * pi * i / n), sin(2 * pi * i / n)) for i in range(n)]


def capsule(p0, p1, r0, r1, n=10):
    d = p1 - p0
    L = hypot(*d)
    if L < 1e-3:
        return circle(p0, max(r0, r1))
    a = atan2(d[1], d[0])
    pts = []
    for i in range(n + 1):  # cap around p1
        t = a - pi / 2 + pi * i / n
        pts.append(p1 + r1 * V(cos(t), sin(t)))
    for i in range(n + 1):  # cap around p0
        t = a + pi / 2 + pi * i / n
        pts.append(p0 + r0 * V(cos(t), sin(t)))
    return pts


def local(origin, axis_deg, pts):
    """Points given in a part frame (u forward/along, v up) placed at origin, rotated by axis_deg."""
    a = radians(axis_deg)
    return [origin + rot(V(*p), a) for p in pts]


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, phase):
        self.px = np.zeros((F, F, 4), np.uint8)
        self.phase = phase

    def to_px(self, p):
        return (AX + p[0], GY + 0.5 - p[1])

    def mask(self, polys):
        im = Image.new("L", (F, F), 0)
        d = ImageDraw.Draw(im)
        for poly in polys:
            d.polygon([self.to_px(p) for p in poly], fill=255)
        return np.array(im) > 0

    def part(self, polys, ramp, light=(1, -1), line=True, flat=False, hi=True, band=0):
        m = self.mask(polys) if not isinstance(polys, np.ndarray) else polys
        self.shade(m, RAMP[ramp] if isinstance(ramp, str) else ramp, light, line, flat, hi, band)
        return m

    def shade(self, m, R, light=(1, -1), line=True, flat=False, hi=True, band=0):
        H, W = m.shape

        def sh(dx, dy):  # value of mask at (x+dx, y+dy) aligned to (x, y)
            out = np.zeros_like(m)
            ys = slice(max(0, -dy), H - max(0, dy))
            yd = slice(max(0, dy), H - max(0, -dy))
            xs = slice(max(0, -dx), W - max(0, dx))
            xd = slice(max(0, dx), W - max(0, -dx))
            out[ys, xs] = m[yd, xd]
            return out

        lx, ly = light
        lvl = np.full(m.shape, 2, np.int8)
        if not flat:
            lit = ~sh(lx, ly) | ~sh(0, ly)
            lvl[lit] = 3
            if hi:
                lvl[~sh(lx, ly) & ~sh(0, ly) & ~sh(lx, 0)] = 4
            dark = ~sh(-lx, -ly) | ~sh(-lx * 2, -ly * 2)
            lvl[dark & ~lit] = 1
            if band:
                # a wider form shadow on the back side, dithered at its inner edge
                yy, xx = np.indices(m.shape)
                deep = np.zeros_like(m)
                for k in range(3, band + 1):
                    deep |= ~sh(-lx * k, 0)
                edge_d = deep & ~sh(-lx * (band - 1), 0) & ~dark
                lvl[deep & ~lit & ~edge_d] = 1
                lvl[edge_d & ((xx + yy) % 2 == 0) & ~lit] = 1
        col = np.array(R)[lvl]
        if line:
            painted = self.px[..., 3] > 0
            edge = m & ((~sh(1, 0) & sh_painted(painted, 1, 0)) | (~sh(-1, 0) & sh_painted(painted, -1, 0)) |
                        (~sh(0, 1) & sh_painted(painted, 0, 1)) | (~sh(0, -1) & sh_painted(painted, 0, -1)))
            col[edge] = R[0]
        self.px[m] = col[m]

    def put(self, p, c, w=1, h=1):
        x, y = self.to_px(p)
        x, y = int(round(x - 0.5)), int(round(y - 0.5))
        self.px[max(0, y):max(0, y + h), max(0, x):max(0, x + w)] = c

    def put_px(self, x, y, c):
        if 0 <= x < F and 0 <= y < F:
            self.px[y, x] = c

    def outline(self, col):
        a = self.px[..., 3] > 0
        n = np.zeros_like(a)
        n[1:, :] |= a[:-1, :]
        n[:-1, :] |= a[1:, :]
        n[:, 1:] |= a[:, :-1]
        n[:, :-1] |= a[:, 1:]
        self.px[n & ~a] = col

    def image(self):
        return Image.fromarray(self.px, "RGBA")


def sh_painted(p, dx, dy):
    H, W = p.shape
    out = np.zeros_like(p)
    ys = slice(max(0, -dy), H - max(0, dy))
    yd = slice(max(0, dy), H - max(0, -dy))
    xs = slice(max(0, -dx), W - max(0, dx))
    xd = slice(max(0, dx), W - max(0, -dx))
    out[ys, xs] = p[yd, xd]
    return out
