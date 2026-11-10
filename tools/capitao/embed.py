"""Embed the rendered sheets into index.html: python3 embed.py <sheets dir> <index.html>.

Replaces the 30 zk{1,2,3}_<Anim> entries of SHEETS (lossless WebP, data URL) and their frame counts.
"""
import base64
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image


def main(src, html):
    src, html = Path(src), Path(html)
    meta = json.loads((src / "meta.json").read_text())
    text = html.read_text()
    done = 0
    for key, m in meta.items():
        buf = io.BytesIO()
        Image.open(src / f"{key}.png").save(buf, "WEBP", lossless=True, quality=100, method=6)
        b64 = base64.b64encode(buf.getvalue()).decode()
        pat = re.compile(r'"%s": \{ "n": \d+, "f": \d+, "ax": \d+, "src": "data:image/webp;base64,[A-Za-z0-9+/=]+" \}' % key)
        new = '"%s": { "n": %d, "f": %d, "ax": %d, "src": "data:image/webp;base64,%s" }' % (key, m["n"], m["f"], m["ax"], b64)
        text, k = pat.subn(lambda _: new, text)
        if k != 1:
            raise SystemExit(f"{key}: expected 1 entry, found {k}")
        done += 1
    html.write_text(text)
    print(f"{done} sheets embedded")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
