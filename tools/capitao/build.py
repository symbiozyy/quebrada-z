"""Render every Capitão sheet: python3 build.py <outdir>  (writes zk{1,2,3}_<Anim>.png + meta.json)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from rig import F, AX, GY, Canvas, OUTLINE
from body import draw, draw_pool, V
from anims import ANIMS, COUNTS, dead


def lying(ph, pose):
    """Dead, second half: the kneeling body keels over backwards onto the ground."""
    k = pose["lying"]
    kneel = dead(ph, 1, 2)                      # the fully buckled pose
    kneel["fx"] = [f for f in kneel["fx"] if f[0] == "aura" and k < 0.4]
    img, _ = draw(kneel, ph)
    angle = 90 * min(1.0, k * 1.15)
    pivot = (AX - 6, GY)
    big = Image.new("RGBA", (F * 2, F * 2))
    big.paste(img, (F // 2, F // 2))
    rot = big.rotate(angle, resample=Image.NEAREST, center=(pivot[0] + F // 2, pivot[1] + F // 2))
    bb = rot.getbbox()
    out = Image.new("RGBA", (F, F))
    if bb:
        crop = rot.crop(bb)
        x = int(round(AX - crop.width * (0.35 + 0.25 * k)))
        y = GY + 1 - crop.height
        out.alpha_composite(crop, (max(0, x), y))
    under = Canvas(ph)
    for f in pose["fx"]:
        if f[0] == "pool":
            draw_pool(under, f[1], f[2])
    base = under.image()
    base.alpha_composite(out)
    return base


def render(ph, anim, i, n):
    pose = ANIMS[anim](ph, i, n)
    if "lying" in pose:
        return lying(ph, pose), {}
    return draw(pose, ph)


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    meta = {}
    for ph in (1, 2, 3):
        for anim, n in COUNTS[ph].items():
            sheet = Image.new("RGBA", (F * n, F))
            info = []
            for i in range(n):
                img, m = render(ph, anim, i, n)
                sheet.alpha_composite(img, (i * F, 0))
                if "muzzle" in m:
                    info.append([round(float(m["muzzle"][0]), 1), round(float(m["muzzle"][1]), 1)])
            key = f"zk{ph}_{anim}"
            sheet.save(out / f"{key}.png")
            meta[key] = {"n": n, "f": F, "ax": AX, "muzzle": info}
    (out / "meta.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
