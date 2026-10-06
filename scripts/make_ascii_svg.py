"""Convert source-prepped.png into a self-typing monochrome ASCII SVG.

Rendered light-on-dark, so the ramp is inverted versus the classic tutorial:
bright pixels get dense glyphs, background (alpha) becomes spaces.
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

RAMP = " .`:-=+*cs#%@"  # sparse -> dense
COLS = 100
CELL_W, CELL_H = 7.4, 14.0
PAD = 20
BG, FG, CURSOR = "#0d1117", "#c9d1d9", "#39d353"
GAMMA = 0.85  # < 1 lifts mid-tones so the dark hoodie still prints a texture
ROW_STAGGER, ROW_DUR = 0.045, 0.32
STATIC = os.environ.get("STATIC") == "1"


def to_rows(path: Path) -> list[str]:
    img = Image.open(path).convert("LA")
    w, h = img.size
    rows = round(h / w * COLS * CELL_W / CELL_H)
    small = np.asarray(img.resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255
    lum, alpha = small[:, :, 0] ** GAMMA, small[:, :, 1]
    idx = 1 + np.rint(lum * (len(RAMP) - 2)).astype(int)
    idx[alpha < 0.5] = 0
    lines = ["".join(RAMP[i] for i in row).rstrip() for row in idx]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def build(lines: list[str]) -> str:
    width = COLS * CELL_W + 2 * PAD
    height = len(lines) * CELL_H + 2 * PAD
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" aria-label="ASCII portrait">',
        f'<rect width="100%" height="100%" rx="12" fill="{BG}"/>',
        "<defs>",
    ]
    body = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped:
            continue
        lead = len(line) - len(stripped)
        x0 = PAD + lead * CELL_W
        span = len(stripped) * CELL_W
        y = PAD + (i + 1) * CELL_H - 3
        begin = i * ROW_STAGGER
        text = (
            f'<text x="{x0:.1f}" y="{y:.1f}" textLength="{span:.1f}" lengthAdjust="spacingAndGlyphs" '
            f'xml:space="preserve">{escape(stripped)}</text>'
        )
        if STATIC:
            body.append(text)
            continue
        out.append(
            f'<clipPath id="r{i}"><rect x="{x0:.1f}" y="{y - CELL_H + 3:.1f}" width="0" height="{CELL_H}">'
            f'<animate attributeName="width" from="0" to="{span:.1f}" begin="{begin:.2f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(f'<g clip-path="url(#r{i})">{text}</g>')
        # curseur bloc qui suit le bord de l'essuyage, puis disparaît
        body.append(
            f'<rect x="{x0:.1f}" y="{y - CELL_H + 4:.1f}" width="{CELL_W:.1f}" height="{CELL_H - 2}" '
            f'fill="{CURSOR}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="{x0:.1f}" to="{x0 + span:.1f}" begin="{begin:.2f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.2f}s"/></rect>'
        )
    out.append("</defs>")
    out.append(
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="12" fill="{FG}">'
    )
    out.extend(body)
    out.append("</g></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    lines = to_rows(ROOT / "source-prepped.png")
    (ROOT / "ascii-portrait.svg").write_text(build(lines))
    print(f"wrote ascii-portrait.svg ({len(lines)} rows)")
