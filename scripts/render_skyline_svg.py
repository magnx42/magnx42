"""Render data/contributions.json as an isometric skyline SVG whose bars rise in a wave."""
import json
import math
from datetime import date
from pathlib import Path

from render_heatmap_svg import ACCENT, BG, FG, FONT, MONTHS, MUTED, PALETTE, levels

ROOT = Path(__file__).resolve().parent.parent

WIDTH = 1720
PAD = 60
YAW, ELEV = math.pi / 4, math.radians(34)
CS, SN = math.cos(YAW), math.sin(YAW)
SE, CE = math.sin(ELEV), math.cos(ELEV)
CELL_W = 0.86  # part de la case occupée par la barre, le reste fait la rue
MAX_H = 7.2  # hauteur du jour le plus chargé, en cases
RISE_S, WAVE_S, START_S = 0.9, 1.7, 0.4


def project(x: float, y: float, z: float) -> tuple[float, float]:
    """Monde (x = semaine, y = jour, z = hauteur) -> écran, avant mise à l'échelle."""
    return x * CS - y * SN, (x * SN + y * CS) * SE - z * CE


def shade(hex_color: str, k: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"#{round(r * k):02x}{round(g * k):02x}{round(b * k):02x}"


def bar_height(count: int, top: int) -> float:
    # racine : un jour à 100 ne doit pas écraser tous les jours à 1-5
    return 0.3 + math.sqrt(count / top) * MAX_H if count and top else 0.15


def streak_range(days: list[dict], length: int, current: bool) -> str:
    """Retrouve les dates de la série (la plus longue, ou celle qui touche aujourd'hui)."""
    if not length:
        return "—"
    counts = [d["count"] for d in days]
    if current:
        end = len(days) - 1 if counts[-1] else len(days) - 2
    else:
        run, end = 0, 0
        for i, c in enumerate(counts):
            run = run + 1 if c else 0
            if run == length:
                end = i
                break
    return f"{fmt(days[end - length + 1]['date'])} — {fmt(days[end]['date'])}"


def fmt(iso: str, year: bool = False) -> str:
    d = date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.day}" + (f", {d.year}" if year else "")


def stat(x: float, y: float, label: str, value: str, unit: str, sub: str, anchor: str) -> str:
    """Label, puis gros chiffre suivi de l'unité et de sa date ; calé à droite (end) ou à gauche (start)."""
    mono = 0.6  # largeur d'un glyphe monospace, en em : assez fiable pour caler du texte
    side = max(len(unit) * 26, len(sub) * 20) * mono
    num = len(value) * 76 * mono
    vx = x - side - 14 - num if anchor == "end" else x
    ux = vx + num + 14
    return (
        f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" fill="{MUTED}" font-size="22">{label}</text>'
        f'<text x="{vx:.0f}" y="{y + 82:.0f}" fill="{ACCENT}" font-size="76" font-weight="700">{value}</text>'
        f'<text x="{ux:.0f}" y="{y + 56:.0f}" fill="{FG}" font-size="26">{unit}</text>'
        f'<text x="{ux:.0f}" y="{y + 82:.0f}" fill="{MUTED}" font-size="20">{sub}</text>'
    )


def main() -> None:
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    days, s = data["days"], data["stats"]
    lv = levels(days)
    top = max(d["count"] for d in days)
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # ligne 0 = dimanche, comme GitHub
    weeks = (len(days) + offset + 6) // 7
    off = (1 - CELL_W) / 2

    bars = []
    for i, (d, level) in enumerate(zip(days, lv)):
        w, wd = divmod(i + offset, 7)
        bars.append((w, wd, bar_height(d["count"], top), level))

    # cadrage : on borne la scène complète, barres à pleine hauteur + rangée de mois devant
    pts = [project(w + dx, wd + dy, h * dz) for w, wd, h, _ in bars for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
    pts += [project(0, 8.6, 0), project(weeks, 8.6, 0)]
    minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
    miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
    scale = (WIDTH - 2 * PAD) / (maxx - minx)
    height = round((maxy - miny) * scale + 2 * PAD)
    ox, oy = PAD - minx * scale, PAD - miny * scale

    def P(x: float, y: float, z: float) -> tuple[float, float]:
        px, py = project(x, y, z)
        return ox + px * scale, oy + py * scale

    # peintre : du plus loin au plus proche (profondeur = x·sin + y·cos)
    bars.sort(key=lambda b: (b[0] + 0.5) * SN + (b[1] + 0.5) * CS)
    out = []
    for w, wd, h, level in bars:
        x0, y0 = w + off, wd + off
        x1, y1 = x0 + CELL_W, y0 + CELL_W
        lift = h * CE * scale  # hauteur à l'écran
        delay = START_S + w / max(1, weeks - 1) * WAVE_S + wd * 0.025
        color = PALETTE[level]
        # faces latérales : rectangle cisaillé, qui grandit depuis le sol par scaleY
        faces = []
        for (ax, ay), (bx, by), k in (
            (P(x0, y1, 0), P(x1, y1, 0), 0.84),
            (P(x1, y1, 0), P(x1, y0, 0), 0.68),
        ):
            skew = math.degrees(math.atan2(by - ay, bx - ax))
            faces.append(
                f'<g transform="translate({ax:.1f} {ay:.1f}) skewY({skew:.2f})">'
                f'<rect class="s" style="animation-delay:{delay:.3f}s" y="{-lift:.1f}" width="{bx - ax:.1f}" height="{lift:.1f}" fill="{shade(color, k)}"/></g>'
            )
        quad = " ".join(f"{a:.1f},{b:.1f}" for a, b in (P(x0, y0, h), P(x1, y0, h), P(x1, y1, h), P(x0, y1, h)))
        out.append(
            f'{"".join(faces)}<polygon class="t" style="--h:{lift:.1f}px;animation-delay:{delay:.3f}s" '
            f'points="{quad}" fill="{color}"/>'
        )

    # mois le long de l'arête avant
    labels, last, edge = [], None, -1e9
    for i, d in enumerate(days):
        w, wd = divmod(i + offset, 7)
        m = d["date"][:7]
        if wd == 0 and m != last and w < weeks - 1:
            x, y = P(w + 0.5, 7.5, 0)
            if x > edge:
                labels.append(f'<text x="{x:.0f}" y="{y + 26:.0f}">{MONTHS[int(m[5:]) - 1]}</text>')
                edge = x + 70
            last = m

    best = s["best_day"]
    stats_tr = stat(
        WIDTH - PAD, PAD + 10, "1 year total", f'{s["total"]:,}', "contributions",
        f'{fmt(days[0]["date"], True)} — {fmt(days[-1]["date"], True)}', "end",
    ) + stat(
        WIDTH - PAD, PAD + 170, "Busiest day", str(best["count"]), "contributions", fmt(best["date"]), "end",
    )
    stats_bl = stat(
        PAD, height - PAD - 270, "Longest streak", str(s["longest_streak"]), "days",
        streak_range(days, s["longest_streak"], False), "start",
    ) + stat(
        PAD, height - PAD - 120, "Current streak", str(s["current_streak"]), "days",
        streak_range(days, s["current_streak"], True), "start",
    )

    end_s = START_S + WAVE_S + RISE_S
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" role="img" aria-label="{s['total']} GitHub contributions in the last year, shown as an isometric skyline">
<style>
.s, .t {{ animation-duration: {RISE_S}s; animation-timing-function: cubic-bezier(.2,.8,.2,1); animation-fill-mode: both; }}
.s {{ transform-box: view-box; transform-origin: 0 0; animation-name: grow; }}
.t {{ animation-name: rise; }}
@keyframes grow {{ from {{ transform: scaleY(0); }} }}
@keyframes rise {{ from {{ transform: translateY(var(--h)); }} }}
.f {{ opacity: 0; animation: fade .7s ease-out forwards; }}
@keyframes fade {{ to {{ opacity: 1; }} }}
@media (prefers-reduced-motion: reduce) {{ .s, .t, .f {{ animation: none; opacity: 1; }} }}
</style>
<rect width="100%" height="100%" rx="16" fill="{BG}"/>
<g>{''.join(out)}</g>
<g class="f" style="animation-delay:{end_s - 0.6:.2f}s" font-family="{FONT}" font-size="20" fill="{MUTED}">{''.join(labels)}</g>
<g class="f" style="animation-delay:{end_s - 0.3:.2f}s" font-family="{FONT}">{stats_tr}</g>
<g class="f" style="animation-delay:{end_s:.2f}s" font-family="{FONT}">{stats_bl}</g>
</svg>"""
    (ROOT / "contrib-skyline.svg").write_text(svg)
    print(f"wrote contrib-skyline.svg ({weeks} weeks, {len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
