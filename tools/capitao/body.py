"""The Capitão's body: one skeleton, three states of ruin.

A pose is a dict (see `base_pose`): pelvis position, torso lean, foot targets, hand targets or
arm angles, rifle placement, head tilt and per-frame effects. `draw(pose, phase)` returns a
176x176 RGBA frame.
"""
from math import radians, sin, cos

import numpy as np

from rig import (Canvas, V, ang, ik, knee_fwd, elbow_down, capsule, circle, local, rot, RAMP,
                 OUTLINE, FLASH, EYE, EYE_HOT, hx)
from heads import draw_head

# body build per phase: limb lengths, radii, torso widths
BUILD = {
    1: dict(thigh=19, shin=19, up=16, fore=15, rleg=(6.0, 4.8, 4.2), rarm=(4.6, 4.0, 3.4), torso=30, tw=(8.5, 11.5, 10), hand=3.0),
    2: dict(thigh=19, shin=19, up=16, fore=15, rleg=(6.0, 4.8, 4.2), rarm=(4.6, 4.0, 3.4), torso=29, tw=(8.5, 11.5, 10), hand=3.0),
    3: dict(thigh=20, shin=20, up=18, fore=17, rleg=(6.6, 5.4, 4.6), rarm=(5.2, 4.4, 4.8), torso=32, tw=(9.5, 13.5, 11.5), hand=3.6),
}


def base_pose(phase):
    lean = {1: 4, 2: 9, 3: 15}[phase]
    hip_y = {1: 40, 2: 39, 3: 40}[phase]
    return dict(
        hip=V(0, hip_y), lean=lean, tilt=0,
        foot_f=V(7, 0), foot_b=V(-7, 0), fa_f=0, fa_b=0,  # foot targets (ankle on ground = y 0) and sole angles
        hand_f=None, hand_b=None,                          # hand targets; None -> use arm angles
        arm_f=(10, 30), arm_b=(-5, 20),                     # (upper, fore) absolute limb angles
        rifle=None,                                         # dict(at=V, deg=angle) grip position + barrel angle
        fx=[],                                              # extra effects
    )


# rifle drawn in its own frame: u along the barrel (forward), v up; origin at the pistol grip top
RIFLE = {
    "stock":  [(-23, 1), (-11, 2.5), (-10, -2), (-13, -3), (-23, -4)],
    "recv":   [(-11, 3), (8, 3), (8, -1.5), (-11, -1.5)],
    "grip":   [(-1, -1), (2, -1), (0.5, -6), (-2.5, -6)],
    "mag":    [(3, -1), (7, -1), (8.5, -8), (4.5, -8.5)],
    "guard":  [(8, 2.5), (21, 2.5), (21, -1.5), (8, -1.5)],
    "barrel": [(21, 1.2), (28, 1.2), (28, -0.6), (21, -0.6)],
    "sight":  [(-3, 3), (2, 3), (2, 5), (-3, 5)],
    "fsight": [(18, 2.5), (20, 2.5), (20, 4.5), (18, 4.5)],
}
FOREGRIP = V(15, -1)
MUZZLE = V(29, 0.5)


def rifle_pt(rf, p):
    return rf["at"] + rot(V(*p), radians(rf["deg"]))


def draw_rifle(cv, rf, mag=True):
    o, d = rf["at"], rf["deg"]
    parts = ["stock", "recv", "grip", "guard", "barrel", "sight", "fsight"]
    if mag and rf.get("mag", True):
        parts.insert(3, "mag")
    for k in parts:
        cv.part([local(o, d, RIFLE[k])], "metal", hi=False)
    # a worn bone-coloured skull decal on the stock: the unit's mark
    cv.put(rifle_pt(rf, (-18, 0)), RAMP["bone"][2])


def draw_flash(cv, p, deg, size):
    for i, (r, c) in enumerate([(size, FLASH[2]), (size * 0.65, FLASH[1]), (size * 0.32, FLASH[0])]):
        pts = [p + rot(V(r * 1.6, 0), radians(deg)), p + rot(V(0, r * 0.7), radians(deg)),
               p + rot(V(-r * 0.3, 0), radians(deg)), p + rot(V(0, -r * 0.7), radians(deg))]
        cv.part([pts], [c] * 5, flat=True, line=False)


def leg(cv, hip, foot, fa, B, phase, near):
    j, end = ik(hip, foot + V(0, 5), B["thigh"], B["shin"], knee_fwd)
    r0, r1, r2 = B["rleg"]
    cv.part([capsule(hip, j, r0, r1)], "uni")
    cv.part([capsule(j, end, r1, r2)], "uni")
    # knee pad (same in every phase: he is still the same unit)
    kp = j + rot(V(1.5, 0), 0)
    cv.part([circle(kp + V(1, 0), 3.4, 10)], "vest")
    # boot: sole from heel to toe, rotated by fa around the ankle
    a = radians(fa)
    sole = [(-4, 4), (3, 4), (6, 3), (9.5, 1), (9.5, -5), (-4.5, -5)]
    pts = [end + rot(V(x, y), a) for x, y in sole]
    cv.part([pts], "boot")
    return j, end


def arm(cv, sh, pose_hand, angles, B, ramp_up, ramp_fore, hand_ramp, pick=elbow_down):
    if pose_hand is not None:
        el, hd = ik(sh, pose_hand, B["up"], B["fore"], pick)
    else:
        el = sh + ang(angles[0]) * B["up"]
        hd = el + ang(angles[1]) * B["fore"]
    r0, r1, r2 = B["rarm"]
    cv.part([capsule(sh, el, r0, r1)], ramp_up)
    cv.part([capsule(el, hd, r1, r2)], ramp_fore)
    cv.part([circle(hd, B["hand"], 10)], hand_ramp)
    if ramp_up == "flesh":
        vein_line(cv, sh, el, 1.2)
        vein_line(cv, el, hd, -1.0)
    if hand_ramp == "flesh":
        d = hd - el
        d = d / max(1e-3, (d[0] ** 2 + d[1] ** 2) ** 0.5)
        for k in (-1, 0, 1):
            p0 = hd + d * (B["hand"] - 0.5) + V(-d[1], d[0]) * k * 1.6
            cv.part([[p0 + V(-d[1], d[0]) * 0.8, p0 - V(-d[1], d[0]) * 0.8, p0 + d * 3.2]], "bone", hi=False, line=False)
    return el, hd


def torso_frame(hip, lean, L):
    a = radians(-lean)   # lean forward = rotate the up-axis towards +x
    up = rot(V(0, 1), a)
    fw = rot(V(1, 0), a)
    return lambda u, v: hip + up * (u * L) + fw * v


def draw(pose, phase, extra=None):
    B = BUILD[phase]
    cv = Canvas(phase)
    hip = pose["hip"]
    T = torso_frame(hip, pose["lean"], B["torso"])
    bw, cw, sw = B["tw"]
    sh_f = T(0.9, 1.0) if phase < 3 else T(0.86, 2.0)
    sh_b = T(0.9, -2.5) if phase < 3 else T(0.84, -3.5)
    neck = T(1.0, 1.5)
    arm_ramp = {1: ("uni", "uni", "glove"), 2: ("uni", "uni", "glove"), 3: ("flesh", "flesh", "flesh")}[phase]
    far_ramp = {1: ("uni", "uni", "glove"), 2: ("uni", "uni", "glove"), 3: ("flesh", "flesh", "flesh")}[phase]

    for fx in pose["fx"]:
        if fx[0] == "aura":
            draw_aura(cv, hip, fx[1])

    # far arm, then far leg (behind everything)
    hb = pose["hand_b"]
    if pose["rifle"] is not None and isinstance(hb, str) and hb == "fore":
        hb = rifle_pt(pose["rifle"], FOREGRIP)
    elif pose["rifle"] is not None and isinstance(hb, str) and hb == "grip_b":
        hb = rifle_pt(pose["rifle"], (0, -2.5))
    elb_b, hand_b = arm(cv, sh_b, hb, pose["arm_b"], B, *far_ramp, pick=pose.get("pick_b", elbow_down))
    leg(cv, hip + V(-2, 0), pose["foot_b"], pose["fa_b"], B, phase, False)

    # pelvis + torso
    pelvis = [T(-0.05, -bw), T(-0.05, bw), T(0.25, bw + 0.5), T(0.25, -bw - 0.5)]
    cv.part([pelvis], "uni")
    leg(cv, hip + V(1, 0), pose["foot_f"], pose["fa_f"], B, phase, True)

    chest = [T(0.18, -bw), T(0.18, bw + 0.5), T(0.62, cw), T(0.85, sw + 0.5), T(1.0, sw - 3),
             T(1.02, -sw + 2), T(0.8, -sw - 1), T(0.5, -bw - 1)]
    if phase == 3:
        draw_rage_torso(cv, T, B)
    else:
        cv.part([chest], "uni")
        draw_vest(cv, T, B, phase)
    # belt (identical in every phase)
    belt = [T(0.16, -bw - 1), T(0.16, bw + 1.5), T(0.25, bw + 1.5), T(0.25, -bw - 1)]
    cv.part([belt], "gear", flat=False)
    cv.put(T(0.205, bw - 1), RAMP["bone"][3], 2, 2)   # buckle
    cv.part([[T(0.07, bw - 5), T(0.07, bw - 1), T(0.2, bw - 0.5), T(0.2, bw - 5)]], "gear")  # thigh pouch

    # head
    draw_head(cv, neck + (V(2, 2) if phase == 3 else V(0, -1)), phase, pose.get("tilt", 0))

    # rifle and near arm
    if pose["rifle"] is not None:
        draw_rifle(cv, dict(pose["rifle"], mag=pose["rifle"].get("mag", True)))
    hf = pose["hand_f"]
    if pose["rifle"] is not None and isinstance(hf, str) and hf == "grip":
        hf = rifle_pt(pose["rifle"], (0, -2.5))
    elb_f, hand_f = arm(cv, sh_f, hf, pose["arm_f"], B, *arm_ramp, pick=pose.get("pick_f", elbow_down))
    draw_shoulder(cv, sh_f, elb_f, phase)
    if phase == 2:
        # torn near sleeve: rotten forearm shows, a bandage strip and blood at the tear
        cv.put(elb_f + (hand_f - elb_f) * 0.15, RAMP["blood"][2], 2, 1)
    for fx in pose["fx"]:
        if fx[0] == "flash":
            draw_flash(cv, rifle_pt(pose["rifle"], MUZZLE + V(1, 0)), pose["rifle"]["deg"], fx[1])
        elif fx[0] == "blood_orb":
            draw_orb(cv, hand_f + V(*fx[2]) if len(fx) > 2 else hand_f, fx[1])
        elif fx[0] == "grenade":
            p = hand_f + V(0, 2.5)
            cv.part([circle(p, 2.6, 8)], "vest")
            cv.put(p + V(0, 2.5), RAMP["metal"][3], 1, 2)
        elif fx[0] == "dust":
            draw_dust(cv, fx[1], fx[2])
        elif fx[0] == "pool":
            draw_pool(cv, fx[1], fx[2])
    cv.outline(OUTLINE[phase])
    if phase == 3:
        heat_glow(cv, max([fx[1] for fx in pose["fx"] if fx[0] == "aura"] or [0]))
        glow_eyes(cv)
    for fx in pose["fx"]:
        if fx[0] == "spray":
            draw_spray(cv, fx[1] if fx[1] is not None else hand_f + V(4, 0), fx[2], fx[3])
    return cv.image(), {"hand_f": hand_f, "hand_b": hand_b, "neck": neck,
                        "muzzle": rifle_pt(pose["rifle"], MUZZLE) if pose["rifle"] is not None else hand_f}


def draw_vest(cv, T, B, phase):
    bw, cw, sw = B["tw"]
    vest = [T(0.24, -bw - 1.5), T(0.24, bw + 2), T(0.6, cw + 1.5), T(0.86, sw + 1.5), T(0.92, sw - 1),
            T(0.92, -sw + 1), T(0.78, -sw - 2), T(0.45, -bw - 2)]
    cv.part([vest], "vest")
    # front pouches (three mags; phase 2 lost one) and the chest plate
    for k in range(3):
        if phase == 2 and k == 0:
            continue
        u = 0.3
        v0 = bw + 1 - k * 4.2
        cv.part([[T(u, v0 - 3.4), T(u, v0), T(u + 0.2, v0), T(u + 0.2, v0 - 3.4)]], "vest")
    plate = [T(0.62, cw - 4), T(0.62, cw + 1), T(0.84, sw + 1), T(0.84, sw - 4)]
    cv.part([plate], "vest")
    a0, a1 = T(0.9, -sw - 1), T(1.35 if phase == 1 else 1.1, -sw - 3)
    cv.part([capsule(a0, a1, 0.6, 0.5, 4)], "metal", flat=True)
    if phase == 2:
        # torn open over the chest: rotten flesh and blood under the plate, bullet holes
        hole = [T(0.6, cw - 2), T(0.68, cw + 1.5), T(0.8, cw), T(0.74, cw - 4)]
        cv.part([hole], "skin")
        cv.put(T(0.66, cw - 1), RAMP["skin"][0], 2, 1)
        cv.put(T(0.6, cw - 1.5), RAMP["blood"][2], 1, 4)
        cv.put(T(0.56, cw - 2), RAMP["blood"][1], 1, 3)
        for u, v in [(0.45, -2), (0.7, -5), (0.36, 4)]:
            cv.put(T(u, v), RAMP["vest"][0], 2, 2)
            cv.put(T(u - 0.03, v), RAMP["blood"][2], 1, 1)


def vein_line(cv, a, b, side):
    """A glowing vein snaking along a limb (phase 3): a continuous 1px line, hot core in the middle."""
    d = b - a
    L = max(1e-3, (d[0] ** 2 + d[1] ** 2) ** 0.5)
    n = V(-d[1], d[0]) / L
    pts = [a + d * (k / 4) + n * side * (0.9 if k % 2 else -0.3) for k in range(1, 4)]
    seg_line(cv, pts, RAMP["rage"][3], EYE)


def seg_line(cv, pts, col, core=None):
    for k, (p0, p1) in enumerate(zip(pts, pts[1:])):
        steps = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1])) * 2) + 1
        for t in range(steps + 1):
            q = p0 + (p1 - p0) * (t / steps)
            cv.put(q, core if core is not None and k == len(pts) // 2 - 1 and t == steps // 2 else col)


def draw_rage_torso(cv, T, B):
    bw, cw, sw = B["tw"]
    # the uniform top is gone: swollen infected torso, same skin as phase 2's scalp and forearm
    body = [T(0.18, -bw), T(0.18, bw + 0.5), T(0.45, cw - 2), T(0.7, cw + 1), T(0.86, sw + 1.5), T(0.96, sw - 3),
            T(0.95, -sw + 3), T(0.82, -sw - 1.5), T(0.5, -bw - 2)]
    cv.part([body], "flesh", band=4)
    # pec and ab blocks carved with the dark tone
    pec = [T(0.68, cw - 6), T(0.7, cw + 0.5), T(0.86, sw + 1), T(0.88, sw - 6)]
    cv.part([pec], "flesh")
    for k in range(3):
        u = 0.3 + k * 0.11
        cv.part([[T(u, cw - 6.5), T(u, cw - 2.5), T(u + 0.09, cw - 2.5), T(u + 0.09, cw - 6.5)]], "flesh", hi=False)
    # burning veins: the rage running under the skin
    vein = RAMP["rage"][4]
    # muscle separation: under the pec, centre line, ab grid
    for t in range(9):
        cv.put(T(0.67, cw - 6 + t * 0.8), RAMP["flesh"][1])
    for t in range(12):
        cv.put(T(0.28 + t * 0.035, cw - 4.5), RAMP["flesh"][1])
    for path in [[(0.92, -3), (0.84, -1), (0.76, -2), (0.68, 0), (0.6, -1), (0.52, 1)],
                 [(0.8, cw - 8), (0.72, cw - 9), (0.62, cw - 8), (0.55, cw - 10)],
                 [(0.98, 2), (0.9, 4), (0.84, 3)],
                 [(0.95, -sw + 2), (0.85, -sw + 3), (0.75, -sw + 2), (0.62, -sw + 4), (0.5, -bw + 1)],
                 [(0.45, 2), (0.38, 0), (0.3, 1.5)]]:
        seg_line(cv, [T(u, v) for u, v in path], RAMP["rage"][3], EYE)
    # torn trousers top + what is left of the vest: one shoulder strap with the skull patch
    strap = capsule(T(1.0, sw - 4), T(0.3, -bw + 1), 1.2, 1.2, 4)
    cv.part([strap], "vest", flat=True)
    cv.put(T(0.72, -2), RAMP["bone"][3], 2, 2)
    # open wounds where the plates were torn off
    cv.put(T(0.58, cw - 1), RAMP["blood"][2], 2, 3)
    cv.put(T(0.56, cw - 1), RAMP["blood"][1], 1, 1)


def draw_shoulder(cv, sh, el, phase):
    if phase == 3:
        # spikes of bone pushing out of the shoulder
        for k, d in enumerate([(-2, 5), (1, 6), (4, 4)]):
            p0 = sh + V(d[0], 1)
            cv.part([[p0 + V(-1.2, 0), p0 + V(1.2, 0), p0 + V(d[1] * 0.15, d[1])]], "bone", hi=False)
        return
    # shoulder pad with the unit's skull patch
    c = sh + (el - sh) * 0.22
    cv.part([circle(c, 4.6, 12)], "vest")
    cv.put(c + V(-1, 1), RAMP["bone"][3], 3, 2)
    cv.put(c + V(0, -1), RAMP["bone"][2], 1, 1)
    if phase == 2:
        cv.put(c + V(2, 2), RAMP["blood"][2], 2, 1)


def draw_orb(cv, p, r):
    cv.part([circle(p, r, 12)], "blood")
    cv.put(p + V(r * 0.3, r * 0.3), RAMP["blood"][4], 1, 1)


def draw_dust(cv, p, r):
    col = [hx("#3a3530"), hx("#5a534a"), hx("#6e675c"), hx("#857d70"), hx("#9a9282")]
    for k, (dx, rr) in enumerate([(-r, r * 0.45), (-r * 0.5, r * 0.6), (0, r * 0.7), (r * 0.5, r * 0.6), (r, r * 0.45)]):
        cv.part([circle(p + V(dx, rr * 0.6), rr, 10)], col, line=False)


def draw_pool(cv, p, w):
    pts = [p + V(-w, 0.5), p + V(w, 0.5), p + V(w * 0.8, 2.2), p + V(-w * 0.7, 2.4)]
    cv.part([pts], "blood", line=False, hi=False)


def draw_spray(cv, p, n, seed):
    rng = np.random.RandomState(seed)
    for _ in range(n):
        q = p + V(rng.uniform(0, 14), rng.uniform(-4, 4))
        cv.put(q, RAMP["blood"][rng.randint(2, 5)])


def draw_aura(cv, hip, k):
    """Phase 3 rage is drawn after the outline (see heat_glow); nothing to do before the body."""
    return


def heat_glow(cv, k):
    """A dithered dark-red heat haze hugging the silhouette, k in 0..1 is its pulse."""
    if k <= 0.05:
        return
    a = cv.px[..., 3] > 0
    ring1 = np.zeros_like(a)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ring1 |= np.roll(np.roll(a, dy, 0), dx, 1)
    ring2 = np.zeros_like(a)
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2):
            if abs(dx) + abs(dy) <= 3:
                ring2 |= np.roll(np.roll(a, dy, 0), dx, 1)
    yy, xx = np.indices(a.shape)
    inner = ring1 & ~a
    outer = ring2 & ~ring1 & (((xx + yy) % 2) == 0)
    cv.px[inner] = (150, 20, 12, int(90 + 90 * k))
    if k > 0.45:
        cv.px[outer] = (120, 14, 10, int(110 * k))


def glow_eyes(cv):
    """Eyes stay bright in the rage phase: a soft halo around every EYE pixel."""
    eye = np.all(cv.px == np.array(EYE), axis=-1) | np.all(cv.px == np.array(EYE_HOT), axis=-1)
    ys, xs = np.nonzero(eye)
    for y, x in zip(ys, xs):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < cv.px.shape[0] and 0 <= xx < cv.px.shape[1] and cv.px[yy, xx, 3] == 0:
                    cv.px[yy, xx] = (255, 60, 40, 110)
