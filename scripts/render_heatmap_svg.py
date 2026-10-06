"""Render data/contributions.json as an animated 53x7 heatmap SVG."""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, MUTED, FG, ACCENT = "#0d1117", "#7d8590", "#c9d1d9", "#39d353"
CELL, GAP = 24, 6
STEP = CELL + GAP
LEFT, TOP = 70, 70
WIDTH = 1720
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def levels(days: list[dict]) -> list[int]:
    """Quartiles over active days, plus a neon level 5 for the top ~5%."""
    active = sorted(d["count"] for d in days if d["count"])
    if not active:
        return [0] * len(days)

    def q(p: float) -> int:
        return active[min(len(active) - 1, int(p * len(active)))]

    cuts = [q(0.25), q(0.5), q(0.75), q(0.95)]
    return [0 if not d["count"] else 1 + sum(d["count"] > c for c in cuts) for d in days]


def main() -> None:
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    days, s = data["days"], data["stats"]
    lv = levels(days)
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # colonne qui démarre un dimanche, comme GitHub
    weeks = (len(days) + offset + 6) // 7
    grid_w = weeks * STEP - GAP
    left = LEFT + (WIDTH - LEFT - 40 - grid_w) / 2 if grid_w < WIDTH - LEFT - 40 else LEFT
    grid_h = 7 * STEP - GAP
    height = TOP + grid_h + 150

    cells, labels, last_month = [], [], None
    for i, (d, l) in enumerate(zip(days, lv)):
        k = i + offset
        w, wd = divmod(k, 7)
        x, y = left + w * STEP, TOP + wd * STEP
        delay = (w + wd) * 0.018
        title = f'{d["count"]} contribution{"s" * (d["count"] != 1)} on {d["date"]}'
        cells.append(
            f'<rect class="c" x="{x:.0f}" y="{y}" width="{CELL}" height="{CELL}" rx="5" '
            f'fill="{PALETTE[l]}" style="animation-delay:{delay:.3f}s"><title>{title}</title></rect>'
        )
        m = d["date"][:7]
        if wd == 0 or i == 0:
            if m != last_month and (int(d["date"][8:]) <= 7 or i == 0):
                if w < weeks - 2:
                    labels.append(f'<text x="{x:.0f}" y="{TOP - 18}">{MONTHS[int(m[5:]) - 1]}</text>')
                last_month = m

    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        labels.append(f'<text x="{left - 14:.0f}" y="{TOP + wd * STEP + 18}" text-anchor="end">{name}</text>')

    # légende Less -> More
    lx = left + grid_w - (len(PALETTE) * STEP + 110)
    ly = TOP + grid_h + 34
    legend = [f'<text x="{lx:.0f}" y="{ly + 18}">Less</text>']
    for j, color in enumerate(PALETTE):
        legend.append(
            f'<rect x="{lx + 56 + j * STEP:.0f}" y="{ly}" width="{CELL}" height="{CELL}" rx="5" fill="{color}"/>'
        )
    legend.append(f'<text x="{lx + 66 + len(PALETTE) * STEP:.0f}" y="{ly + 18}">More</text>')

    best = s["best_day"]
    footer = (
        f'<tspan fill="{ACCENT}" font-weight="700">{s["total"]:,}</tspan> contributions in the last year'
        f'<tspan fill="{MUTED}">  ·  </tspan>current streak <tspan fill="{FG}">{s["current_streak"]}d</tspan>'
        f'<tspan fill="{MUTED}">  ·  </tspan>longest <tspan fill="{FG}">{s["longest_streak"]}d</tspan>'
        f'<tspan fill="{MUTED}">  ·  </tspan>best day <tspan fill="{FG}">{best["count"]}</tspan>'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" role="img" aria-label="{s['total']} GitHub contributions in the last year">
<style>
.c {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: drop .45s cubic-bezier(.2,.8,.2,1) forwards; }}
@keyframes drop {{ from {{ opacity: 0; transform: translateY(-14px) scale(.6); }} to {{ opacity: 1; transform: none; }} }}
.f {{ opacity: 0; animation: fade .6s ease-out 1.6s forwards; }}
@keyframes fade {{ to {{ opacity: 1; }} }}
@media (prefers-reduced-motion: reduce) {{ .c, .f {{ animation: none; opacity: 1; }} }}
</style>
<rect width="100%" height="100%" rx="16" fill="{BG}"/>
<g font-family="{FONT}" font-size="20" fill="{MUTED}">{''.join(labels)}</g>
<g>{''.join(cells)}</g>
<g class="f" font-family="{FONT}" font-size="20" fill="{MUTED}">
{''.join(legend)}
<text x="{left:.0f}" y="{ly + 18}" fill="{FG}">{footer}</text>
</g>
</svg>"""
    (ROOT / "contrib-heatmap.svg").write_text(svg)
    print(f"wrote contrib-heatmap.svg ({weeks} weeks)")


if __name__ == "__main__":
    main()
