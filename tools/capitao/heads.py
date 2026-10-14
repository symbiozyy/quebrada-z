"""Hand-placed head templates, 3/4 view facing right. One row per string; '.' is empty.

o outline · K/H/h helmet dark/mid/light · u/U balaclava dark/mid · n/b/B/W bone shadow/mid/light/highlight
e socket · r eye · R eye hot · s/S/z skin mid/light/dark · x/X rage skin dark/mid · y crack · d/D blood dark/mid
m strap
The anchor of each template is NECK = (col, row) of the neck's bottom centre.
"""
from rig import RAMP, SOCKET, EYE, EYE_HOT

PAL = {
    "o": RAMP["uni"][0],
    "K": RAMP["boot"][1], "H": RAMP["boot"][2], "h": RAMP["boot"][3], "j": RAMP["boot"][4],
    "u": RAMP["uni"][1], "U": RAMP["uni"][2],
    "n": RAMP["bone"][1], "b": RAMP["bone"][2], "B": RAMP["bone"][3], "W": RAMP["bone"][4],
    "e": SOCKET, "r": EYE, "R": EYE_HOT,
    "z": RAMP["skin"][1], "s": RAMP["skin"][2], "S": RAMP["skin"][3],
    "f": RAMP["flesh"][1], "F": RAMP["flesh"][2], "G": RAMP["flesh"][3],
    "x": RAMP["rage"][3], "X": RAMP["rage"][2], "Y": RAMP["rage"][4],
    "y": RAMP["bone"][0],
    "d": RAMP["blood"][1], "D": RAMP["blood"][2],
    "m": RAMP["gear"][2], "M": RAMP["gear"][1],
}

# phase 1: combat helmet, balaclava, intact skull mask, dim red pupils
H1 = [
    "......ooooooo......",
    "....ooHhhhhhhoo....",
    "...oHHhhhjjhhhHo...",
    "..oHHHhhhhhhhhHHo..",
    "..oKHHHHHHHHHHHHHo.",
    ".oKKKHHHHHHHHHHHHo.",
    ".oKKKKKKKKKKKKKKKKo",
    ".ouuuuuooooooooooo.",
    ".ouuuuuobBBBBBBBWo.",
    "ouuuUuobBBBBBBBBBBo",
    "ouuUUuobeeebBBBeebo",
    "ouuUuuobeeerbBBeero",
    "ouuuuuonbeebbbBbebo",
    "ouumuuonbbbbBnBBbbo",
    ".ouumuonnbbbnenbbo.",
    ".ouuumunbbBbbbBbbo.",
    ".ouuuumonbobobobo..",
    "..ouuuumnbobobobo..",
    "..ouuuuuonnnnnno...",
    "...ouuuuuoooooo....",
    "....ouuuuuuo.......",
]
# phase 2: helmet gone (shaved infected scalp, stitches), mask cracked, chunk missing over the far eye
H2 = [
    "...................",
    "......ooooooo......",
    "....oozsssSSSoo....",
    "...ozssSsSSSSSso...",
    "..ozzsssssssSSSSo..",
    "..ozzsoSoSoSsSSSo..",
    ".ozzzzssssssssSso..",
    ".ozuuuuoooooooooo..",
    ".ouuuuuobBBBBByoso.",
    "ouuuUuobBBBBByysSo.",
    "ouuUUuobeeebBBysrRo",
    "ouuUuuobeeerbyBsrso",
    "ouuuuuonbeebbybBbbo",
    "ouumuuonbbbbBnBBbbo",
    ".ouumuonnbbbnenbdo.",
    ".ouuumunbbBbbbBdDo.",
    ".ouuuumonbobobobDo.",
    "..ouuuumnbobobobdo.",
    "..ouuuuuonnnnnnod..",
    "...ouuuuuoooooo.D..",
    "....ouuuuuuo.......",
]
# phase 3: mask shattered to the jaw-line, both eyes burning, rage-red scalp with veins
H3 = [
    "...................",
    "......ooooooo......",
    "....oofFxFGGGoo....",
    "...ofFFGxGGGGGFo...",
    "..offFxFFxFFFGGGo..",
    "..offFFFFFxFFGGGo..",
    ".offxfFFFFFFxFGFo..",
    ".offffFooooooooFo..",
    ".offffobBByoyBBBo..",
    "offoofobBBBybBBBBo.",
    "ofoFGoobeeeebyBeeeo",
    "ofoFfoobeRRreyBeRRo",
    "offoofonberreybbero",
    "offxffonbbbbBnBBbbo",
    ".offxfonnbbbnenbbdo",
    ".offfxfnbbobobobDDo",
    ".offffonbobobobodDo",
    "..offffonbDbobDbddo",
    "..offfffonnnnnnodd.",
    "...offfffoooooo.D..",
    "....offffffo...D...",
]
NECK = (8, 20)
HEADS = {1: H1, 2: H2, 3: H3}


def draw_head(cv, neck_pt, phase, tilt=0):
    """Blit the head so its NECK cell lands on neck_pt. tilt shifts rows (shear) for nods."""
    rows = HEADS[phase]
    x0, y0 = cv.to_px(neck_pt)
    x0, y0 = int(round(x0)) - NECK[0], int(round(y0)) - NECK[1]
    n = len(rows)
    for r, line in enumerate(rows):
        shift = int(round(tilt * (n - r) / n))
        for c, ch in enumerate(line):
            if ch != ".":
                cv.put_px(x0 + c + shift, y0 + r, PAL[ch])
