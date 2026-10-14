"""Animations: pose(phase, i, n) for every sheet the game plays on the Capitão.

What the game does with each (index.html, updateCap):
  Idle      stalk/recover/smoke, looped at 4-6 fps
  Walk/Run  stalk, enter, charge (Run at 16 fps)
  Attack_1  burst/sweep: frame 0 aim, frames 1 and 2 alternate while firing, frame 3 settle
  Attack_2  grenade, mortar, mines, melee: frame 0 wind-up, frame 2 release
  Special   roar, phase change, recruit, air strike
  Reload    reload (phase 3 has no rifle: he heaves for breath)
  Jump      the generic zombie jump: the game shows frames 2..n-2 in the air
  Hurt      flinch, played once
  Dead      played once, holds the last frame
"""
from math import sin, cos, pi

from body import base_pose, V

COUNTS = {
    1: dict(Idle=7, Walk=8, Run=8, Attack_1=4, Attack_2=4, Special=7, Reload=6, Jump=8, Hurt=3, Dead=4),
    2: dict(Idle=7, Walk=8, Run=8, Attack_1=4, Attack_2=4, Special=7, Reload=6, Jump=8, Hurt=3, Dead=4),
    3: dict(Idle=7, Walk=8, Run=8, Attack_1=4, Attack_2=4, Special=7, Reload=6, Jump=5, Hurt=3, Dead=8),
}


def armed(ph):
    return ph < 3


def low_ready(p, dy=0, deg=-22, dx=0):
    p["rifle"] = dict(at=p["hip"] + V(9 + dx, 20 + dy), deg=deg)
    p["hand_f"] = "grip"
    p["hand_b"] = "fore"


def aim(p, recoil=0, dy=0):
    p["rifle"] = dict(at=p["hip"] + V(13 - recoil, 31 + dy), deg=0)
    p["hand_f"] = "grip"
    p["hand_b"] = "fore"


def gait(p, t, stride, lift, bob, ph):
    """Feet on a cycle: t in [0,1). Front foot leads at t=0."""
    for key, off in (("foot_f", 0.0), ("foot_b", 0.5)):
        a = 2 * pi * (t + off)
        x = stride * cos(a)
        y = lift * max(0.0, sin(a))       # lifted while swinging forward
        p[key] = V(x + 1, y)
        p["fa_f" if key == "foot_f" else "fa_b"] = -10 * max(0.0, sin(a)) + (8 if cos(a) < -0.6 and y < 0.5 else 0)
    p["hip"] = p["hip"] + V(0, -bob * abs(cos(2 * pi * t * 2)) * 0.5 - bob * 0.5 + bob * abs(sin(2 * pi * t * 2)))


def idle(ph, i, n):
    p = base_pose(ph)
    t = i / n
    b = sin(2 * pi * t)
    p["hip"] = p["hip"] + V(0, round(-0.6 + 0.6 * b))
    p["lean"] += 1.2 * b
    p["foot_f"], p["foot_b"] = V(8, 0), V(-6, 0)
    if armed(ph):
        low_ready(p, dy=round(0.8 * b))
    else:
        # hunched, claws twitching, shoulders heaving
        p["arm_f"] = (22 + 4 * b, 38 + 8 * sin(2 * pi * t + 1))
        p["arm_b"] = (2 - 3 * b, 22 + 6 * b)
        p["tilt"] = round(b)
        p["fx"].append(("aura", 0.55 + 0.45 * sin(2 * pi * t)))
    return p


def walk(ph, i, n):
    p = base_pose(ph)
    t = i / n
    gait(p, t, 9 if ph < 3 else 10, 5, 1.5, ph)
    sw = sin(2 * pi * t)
    p["lean"] += 1
    if armed(ph):
        low_ready(p, dy=round(-0.8 * abs(sw)))
    else:
        p["arm_f"] = (14 - 22 * sw, 40 - 14 * sw)
        p["arm_b"] = (6 + 22 * sw, 34 + 10 * sw)
        p["fx"].append(("aura", 0.6))
    return p


def run(ph, i, n):
    p = base_pose(ph)
    t = i / n
    gait(p, t, 14 if ph < 3 else 15, 9, 3, ph)
    sw = sin(2 * pi * t)
    p["lean"] += 10
    p["hip"] = p["hip"] + V(2, -1)
    if armed(ph):
        # port arms: rifle across the chest, muzzle up
        p["rifle"] = dict(at=p["hip"] + V(12, 22 + round(sw)), deg=28)
        p["hand_f"] = "grip"
        p["hand_b"] = "fore"
    else:
        p["arm_f"] = (40 - 55 * sw, 95 - 40 * sw)
        p["arm_b"] = (40 + 55 * sw, 95 + 40 * sw)
        p["fx"].append(("aura", 0.8))
    return p


def attack_1(ph, i, n):
    """Burst: 0 aim, 1/2 firing (alternate), 3 settle. Phase 3 hurls blood bolts instead."""
    p = base_pose(ph)
    p["foot_f"], p["foot_b"] = V(11, 0), V(-9, 0)
    p["fa_b"] = 4
    if armed(ph):
        rec = {0: 0, 1: 2, 2: 1, 3: 0}[i]
        aim(p, recoil=rec)
        p["lean"] = {1: 2, 2: 6}[ph] - rec
        if i in (1, 2):
            p["fx"].append(("flash", 5 if i == 1 else 3.6))
    else:
        p["fx"].append(("aura", 0.9))
        if i == 0:      # wind-up: hand back, bolt forming
            p["arm_f"] = (-60, -10)
            p["lean"] -= 4
            p["fx"].append(("blood_orb", 3))
        elif i in (1, 2):  # throw: arm snapped forward at shoulder height
            p["arm_f"] = (95, 88 if i == 1 else 96)
            p["lean"] += 6
            p["fx"].append(("blood_orb", 3.5 if i == 1 else 2.6, (3, 0)))
            p["fx"].append(("spray", None, 10 if i == 1 else 6, i))
        else:
            p["arm_f"] = (60, 70)
        p["arm_b"] = (-25, 10)
    return p


def attack_2(ph, i, n):
    """Grenade/mortar/mines/melee: 0 wind-up, 1 swing, 2 release, 3 follow-through."""
    p = base_pose(ph)
    p["foot_f"], p["foot_b"] = V(10, 0), V(-10, 0)
    if armed(ph):
        # rifle hangs in the far hand, the near arm throws
        p["rifle"] = dict(at=p["hip"] + V(-2, 14), deg=-60)
        p["hand_b"] = "grip_b"
        ang_up = [(-150, -110), (-200 + 360, 140), (120, 100), (70, 60)][i]
        p["arm_f"] = ang_up
        p["lean"] += [-6, 0, 8, 6][i]
        if i < 2:
            p["fx"].append(("grenade",))
    else:
        # overhead hammer-fist slam
        up = [(170, 175), (150, 120), (80, 60), (70, 50)][i]
        p["arm_f"] = up
        p["arm_b"] = (up[0] - 15, up[1] - 10)
        p["lean"] += [-8, 4, 22, 16][i]
        p["hip"] = p["hip"] + V(0, [0, 0, -5, -3][i])
        p["fx"].append(("aura", 1.0 if i == 2 else 0.6))
        if i == 2:
            p["fx"].append(("dust", V(22, 0), 6))
    return p


def special(ph, i, n):
    """Roar / call the horde: chest out, head back, fist up (armed) or arms spread (rage)."""
    p = base_pose(ph)
    t = i / (n - 1)
    k = sin(pi * t)                    # 0 -> 1 -> 0 over the cycle
    p["foot_f"], p["foot_b"] = V(10, 0), V(-9, 0)
    p["lean"] -= 10 * k
    p["tilt"] = -round(2 * k)
    if armed(ph):
        p["rifle"] = dict(at=p["hip"] + V(-3, 15), deg=-70)
        p["hand_b"] = "grip_b"
        p["arm_f"] = (60 + 80 * k, 80 + 85 * k)
    else:
        p["arm_f"] = (60 + 70 * k, 70 + 90 * k)
        p["arm_b"] = (-40 - 60 * k, -20 - 90 * k)
        p["hip"] = p["hip"] + V(0, round(2 * k))
        p["fx"].append(("aura", 0.4 + 0.6 * k))
    return p


def reload(ph, i, n):
    p = base_pose(ph)
    p["foot_f"], p["foot_b"] = V(8, 0), V(-7, 0)
    if armed(ph):
        # tilt the rifle, drop the mag, slap a new one in, rack it
        deg = [-10, 10, 18, 18, 12, -5][i]
        p["rifle"] = dict(at=p["hip"] + V(8, 24), deg=deg, mag=i not in (1, 2))
        p["hand_b"] = "fore"
        if i == 1:
            p["hand_f"] = p["hip"] + V(12, 12)       # reaching to the belt
        elif i == 2:
            p["hand_f"] = p["hip"] + V(14, 18)
        elif i == 5:
            p["hand_f"] = p["hip"] + V(4, 30)        # racking the charging handle
        else:
            p["hand_f"] = "grip"
        p["tilt"] = 1 if i in (1, 2, 3) else 0
    else:
        # heaving: hunched over, hands near the knees, aura breathing with him
        b = sin(2 * pi * i / n)
        p["lean"] += 14 + 3 * b
        p["hip"] = p["hip"] + V(0, -3 + round(b))
        p["arm_f"] = (40 + 6 * b, 20 + 5 * b)
        p["arm_b"] = (25 - 4 * b, 10)
        p["fx"].append(("aura", 0.5 + 0.5 * b))
    return p


def jump(ph, i, n):
    p = base_pose(ph)
    t = i / (n - 1)
    crouch = [1, 0.4, 0, 0, 0, 0, 0.3, 1][min(7, round(t * 7))] if n == 8 else [1, 0, 0, 0, 1][i]
    tuck = sin(pi * t)
    p["hip"] = p["hip"] + V(0, -6 * crouch + 2 * tuck)
    p["foot_f"] = V(8 + 2 * tuck, 9 * tuck)
    p["foot_b"] = V(-8 + 4 * tuck, 6 * tuck)
    p["fa_f"], p["fa_b"] = -12 * tuck, 8 * tuck
    p["lean"] += 6 * crouch + 4 * tuck
    if armed(ph):
        low_ready(p, dy=round(4 * tuck - 2 * crouch), deg=-22 + 30 * tuck)
    else:
        p["arm_f"] = (30 + 80 * tuck, 60 + 70 * tuck)
        p["arm_b"] = (10 + 60 * tuck, 40 + 60 * tuck)
        p["fx"].append(("aura", 0.7))
    return p


def hurt(ph, i, n):
    p = base_pose(ph)
    k = [1, 0.75, 0.35][i]
    p["foot_f"], p["foot_b"] = V(9, 0), V(-7, 0)
    p["lean"] -= 14 * k
    p["hip"] = p["hip"] + V(-3 * k, -1)
    p["tilt"] = -round(3 * k)
    if armed(ph):
        low_ready(p, dy=round(3 * k), deg=-22 + 35 * k, dx=-3 * k)
    else:
        p["arm_f"] = (30 + 40 * k, 60 + 50 * k)
        p["arm_b"] = (-10 - 30 * k, 20)
        p["fx"].append(("aura", 1.0 - 0.5 * k))
    return p


def dead(ph, i, n):
    """Falls to his knees then onto his back. The last frame lies flat."""
    p = base_pose(ph)
    t = i / (n - 1)
    p["fx"].append(("aura", max(0.0, 0.8 - t)) if ph == 3 else ("none",))
    if t < 0.5:                     # buckle to the knees
        k = t / 0.5
        p["hip"] = p["hip"] + V(-2 * k, -15 * k)
        p["foot_f"], p["foot_b"] = V(10, 0), V(-8 - 6 * k, 0)
        p["fa_b"] = 50 * k
        p["lean"] += 10 + 8 * k
        p["tilt"] = round(2 * k)
        if armed(ph):
            low_ready(p, dy=-6 * k, deg=-22 - 50 * k)
        else:
            p["arm_f"], p["arm_b"] = (20 + 10 * k, 10), (10, 0)
        return p
    # keel over backwards: the whole body lies down, drawn as a lying pose
    k = (t - 0.5) / 0.5
    p["lying"] = k
    p["fx"].append(("pool", V(-8, 0), 6 + 12 * k))
    return p


ANIMS = dict(Idle=idle, Walk=walk, Run=run, Attack_1=attack_1, Attack_2=attack_2, Special=special,
             Reload=reload, Jump=jump, Hurt=hurt, Dead=dead)
