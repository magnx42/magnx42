"""Hand-authored neofetch-style info card SVG. STATIC=1 emits a frozen frame."""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
STATIC = os.environ.get("STATIC") == "1"

BG, BAR, MUTED, FG = "#0d1117", "#161b22", "#7d8590", "#c9d1d9"
KEY, ACCENT, BLUE = "#39d353", "#69f0a0", "#79c0ff"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
WIDTH, LINE, FS = 980, 42, 24

TITLE = "matis@fluxa"
ROWS: list[tuple[str, str]] = [
    ("Name", "Matis Geneix"),
    ("Now", "Data science · Python · SQL"),
    ("Also", "Co-founder @ FLUXA"),
    ("", "premium web · AI automation · GEO"),
    ("School", "42 Angoulême (C · C++ · Unix)"),
    ("Stack", "Next.js · TypeScript · Supabase"),
    ("Infra", "Docker · Traefik · Cloudflare"),
    ("", None),
    ("Web", "fluxaweb.fr"),
    ("LinkedIn", "in/matis-geneix-4840012a5"),
    ("Location", "France"),
]
SWATCHES = ["#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0", "#79c0ff", "#d2a8ff", "#c9d1d9"]


def main() -> None:
    lines = []
    y = 132
    key_w = 150
    # en-tête façon prompt + séparateur
    lines.append((y, f'<tspan fill="{KEY}" font-weight="700">magnx42</tspan><tspan fill="{FG}">@</tspan>'
                     f'<tspan fill="{KEY}" font-weight="700">github</tspan>'))
    y += LINE
    lines.append((y, f'<tspan fill="{MUTED}">{"─" * 14}</tspan>'))
    for key, value in ROWS:
        y += LINE
        if value is None:
            continue
        k = f'<tspan fill="{KEY}" font-weight="700">{escape(key)}</tspan>' if key else ""
        lines.append((y, f'{k}<tspan x="{60 + key_w + 20}" fill="{FG}">{escape(value)}</tspan>'))
    y += LINE + 10
    sw_y = y
    height = max(sw_y + 90, 822)  # même hauteur rendue que le portrait (370/780 vs 490/980)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" '
        f'role="img" aria-label="Matis Geneix, data science with Python and SQL, co-founder of FLUXA, student at 42 Angoulême">',
        "<style>",
        ".l { opacity: 0; animation: in .45s cubic-bezier(.2,.8,.2,1) forwards; }",
        "@keyframes in { from { opacity: 0; transform: translateX(-12px); } to { opacity: 1; transform: none; } }",
        "@media (prefers-reduced-motion: reduce) { .l { animation: none; opacity: 1; } }",
        "</style>" if not STATIC else "<style>.l{opacity:1}</style>",
        f'<rect width="100%" height="100%" rx="16" fill="{BG}"/>',
        f'<path d="M0 16 a16 16 0 0 1 16 -16 h{WIDTH - 32} a16 16 0 0 1 16 16 v40 h-{WIDTH} z" fill="{BAR}"/>',
    ]
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        out.append(f'<circle cx="{34 + i * 26}" cy="28" r="8" fill="{c}"/>')
    out.append(f'<text x="{WIDTH / 2}" y="36" text-anchor="middle" font-family="{FONT}" font-size="20" '
               f'fill="{MUTED}">{TITLE} — neofetch</text>')
    out.append(f'<g font-family="{FONT}" font-size="{FS}">')
    for n, (ly, content) in enumerate(lines):
        delay = 0.4 + n * 0.12
        style = "" if STATIC else f' style="animation-delay:{delay:.2f}s"'
        out.append(f'<text class="l" x="60" y="{ly}"{style}>{content}</text>')
    sw_delay = 0.4 + len(lines) * 0.12
    style = "" if STATIC else f' style="animation-delay:{sw_delay:.2f}s"'
    out.append(f'<g class="l"{style}>')
    for i, c in enumerate(SWATCHES):
        out.append(f'<rect x="{60 + i * 52}" y="{sw_y}" width="44" height="30" rx="4" fill="{c}"/>')
    out.append("</g>")
    # curseur clignotant en fin de sortie
    cur = f'<rect x="{60 + len(SWATCHES) * 52 + 10}" y="{sw_y}" width="14" height="30" fill="{ACCENT}">'
    if not STATIC:
        cur += (f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.01;0.02;0.5;0.51" '
                f'dur="1.1s" begin="{sw_delay:.2f}s" repeatCount="indefinite"/>')
    out.append(cur + "</rect>")
    out.append("</g></svg>")
    (ROOT / "info-card.svg").write_text("\n".join(out))
    print(f"wrote info-card.svg ({WIDTH}x{height})")


if __name__ == "__main__":
    main()
