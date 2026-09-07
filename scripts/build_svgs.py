#!/usr/bin/env python3
"""Render the vector assets: title card, RECLAIM compute figure, stack strip.

Each is emitted per theme and switched in the README with <picture>.

Motion rule: every animated element is fully visible in its base state and the
keyframes only replay the entrance (fill-mode none, no delay on anything that
carries content). A browser that suspends offscreen image animations, or a
reader with prefers-reduced-motion, still sees the finished figure.
"""
import json
from datetime import date
from math import ceil, hypot
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "Mithil Salunkhe"
TAGLINE = "CS @ Illinois  ·  agent evaluation, ML systems, HPC"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

# One accent hue throughout. Each theme's step clears 4.5:1 on its own surface
# (#b5560c on white = 4.88, #ff9c3d on #0d1117 = 9.08).
THEMES = {
    "dark": dict(ink="#e6edf3", muted="#9198a1", faint="#6e7681",
                 rule="#30363d", grid="#21262d", accent="#ff9c3d", surface="#0d1117"),
    "light": dict(ink="#1f2328", muted="#59636e", faint="#818b98",
                  rule="#d1d9e0", grid="#e6eaef", accent="#b5560c", surface="#ffffff"),
}

REDUCED = ("@media (prefers-reduced-motion:reduce){*{animation:none!important}}")

STACK = ["Python", "PyTorch", "C++", "TypeScript", "CUDA", "Slurm",
         "Apptainer", "vLLM", "Supabase", "three.js"]


def fmt(n):
    if n >= 1e9:
        return f"{n/1e9:.1f}B"
    if n >= 1e6:
        return f"{n/1e6:.1f}M"
    return f"{n:,}"


def title_card(theme, contrib):
    t = THEMES[theme]
    W, H = 1200, 112
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-label="{NAME}. {contrib["total"]:,} contributions '
         f'in the last twelve months.">']
    p.append(f"""<defs><linearGradient id="rl" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{t['accent']}"/>
<stop offset="1" stop-color="{t['accent']}" stop-opacity="0"/></linearGradient></defs>""")
    p.append(f"""<style>
.s{{font-family:{SANS}}}.m{{font-family:{MONO}}}
.sweep{{transform-origin:0 0;transform:scaleX(1);animation:sw .9s cubic-bezier(.2,.8,.3,1)}}
@keyframes sw{{from{{transform:scaleX(0)}}}}
{REDUCED}</style>""")
    p.append(f'<text class="s" x="0" y="48" font-size="42" font-weight="700" '
             f'letter-spacing="-1.3" fill="{t["ink"]}">{NAME}</text>')
    p.append(f'<rect class="sweep" x="0" y="62" width="268" height="2" rx="1" fill="url(#rl)"/>')
    p.append(f'<text class="m" x="0" y="90" font-size="15" fill="{t["muted"]}">{TAGLINE}</text>')
    p.append(f'<text class="m" x="{W}" y="48" font-size="38" font-weight="600" '
             f'text-anchor="end" letter-spacing="-1" fill="{t["ink"]}">{contrib["total"]:,}</text>')
    p.append(f'<text class="m" x="{W}" y="72" font-size="12" letter-spacing="1.1" '
             f'text-anchor="end" fill="{t["faint"]}">CONTRIBUTIONS · LAST 12 MONTHS</text>')
    p.append(f'<text class="m" x="{W}" y="90" font-size="12" letter-spacing="1.1" '
             f'text-anchor="end" fill="{t["faint"]}">{contrib["commits"]:,} COMMITS</text>')
    p.append("</svg>")
    return "\n".join(p)


def compute_figure(theme, r):
    t = THEMES[theme]
    W, H = 1200, 404
    L, R, TOP, BOT = 4, 104, 152, 70
    pw, ph = W - L - R, H - TOP - BOT

    tiles = [(f"{r['runs']:,}", "REPRODUCTION RUNS"),
             (f"{r['models']}", "AGENT MODELS"),
             (fmt(r["tokens"]), "TOKENS"),
             (f"{r['tool_calls']:,}", "TOOL CALLS")]

    daily = r["daily"]
    ymax = max(d["h100"] for d in daily)
    # headroom above the peak so the direct label has somewhere to sit
    ytop = 500 * ceil(ymax * 1.13 / 500)
    x = lambda i: L + pw * i / (len(daily) - 1)
    y = lambda v: TOP + ph - ph * v / ytop

    pts = [(x(i), y(d["h100"])) for i, d in enumerate(daily)]
    line = " ".join(("M" if i == 0 else "L") + f"{a:.1f} {b:.1f}" for i, (a, b) in enumerate(pts))
    area = line + f" L{pts[-1][0]:.1f} {TOP+ph:.1f} L{L} {TOP+ph:.1f} Z"
    length = sum(hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1))

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-label="RECLAIM metered compute. {r["h100_hours"]:,} '
         f'H100-hours across {r["runs"]:,} reproduction runs, {r["window"][0]} to '
         f'{r["window"][1]}.">']
    p.append(f"""<defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{t['accent']}" stop-opacity="0.30"/>
<stop offset="1" stop-color="{t['accent']}" stop-opacity="0.02"/></linearGradient></defs>""")
    p.append(f"""<style>
.s{{font-family:{SANS}}}.m{{font-family:{MONO}}}
.trace{{stroke-dasharray:{length:.0f};stroke-dashoffset:0;animation:dr 1.7s cubic-bezier(.3,.7,.3,1)}}
@keyframes dr{{from{{stroke-dashoffset:{length:.0f}}}}}
.wash{{opacity:1;animation:wa 1.9s ease-out}}
@keyframes wa{{from{{opacity:0}}}}
{REDUCED}</style>""")

    p.append(f'<text class="m" x="{L}" y="18" font-size="12" letter-spacing="1.2" '
             f'fill="{t["faint"]}">RECLAIM · METERED COMPUTE</text>')
    p.append(f'<text class="s" x="{L}" y="52" font-size="26" font-weight="600" '
             f'letter-spacing="-0.5" fill="{t["ink"]}">'
             f'{r["h100_hours"]:,} H100-hours across {r["runs"]:,} reproduction runs</text>')
    p.append(f'<text class="s" x="{L}" y="78" font-size="14" fill="{t["muted"]}">'
             f'Every run is budgeted, metered, and audited from its own execution evidence.</text>')

    tw = (W - L - 4) / len(tiles)
    for i, (val, lab) in enumerate(tiles):
        tx = L + i * tw
        if i:
            p.append(f'<rect x="{tx-16:.0f}" y="100" width="1" height="36" fill="{t["rule"]}"/>')
        p.append(f'<text class="m" x="{tx:.0f}" y="122" font-size="21" font-weight="600" '
                 f'fill="{t["ink"]}">{val}</text>'
                 f'<text class="m" x="{tx:.0f}" y="138" font-size="10.5" letter-spacing="0.9" '
                 f'fill="{t["faint"]}">{lab}</text>')

    for k in range(5):
        v = ytop * k / 4
        gy = y(v)
        p.append(f'<line x1="{L}" y1="{gy:.1f}" x2="{L+pw}" y2="{gy:.1f}" '
                 f'stroke="{t["grid"]}" stroke-width="1"/>')
        p.append(f'<text class="m" x="{L+pw+10}" y="{gy+4:.1f}" font-size="11" '
                 f'fill="{t["faint"]}">{v:,.0f}</text>')

    p.append(f'<path class="wash" d="{area}" fill="url(#fill)"/>')
    p.append(f'<path class="trace" d="{line}" fill="none" stroke="{t["accent"]}" '
             f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')

    # single series, so the end value is direct-labelled instead of legended
    ex, ey = pts[-1]
    p.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{t["accent"]}" '
             f'stroke="{t["surface"]}" stroke-width="2"/>')
    p.append(f'<text class="m" x="{ex:.1f}" y="{ey-14:.1f}" font-size="13" font-weight="600" '
             f'text-anchor="end" fill="{t["ink"]}">{r["h100_hours"]:,} GPU-hours</text>')

    p.append(f'<line x1="{L}" y1="{TOP+ph:.1f}" x2="{L+pw}" y2="{TOP+ph:.1f}" '
             f'stroke="{t["rule"]}" stroke-width="1"/>')
    for i, anchor in ((0, "start"), (len(daily)//2, "middle"), (len(daily)-1, "end")):
        d = date.fromisoformat(daily[i]["date"]).strftime("%b %-d, %Y")
        p.append(f'<text class="m" x="{x(i):.1f}" y="{TOP+ph+20:.0f}" font-size="11" '
                 f'text-anchor="{anchor}" fill="{t["faint"]}">{d}</text>')
    p.append(f'<text class="m" x="{L}" y="{H-8}" font-size="11" fill="{t["faint"]}">'
             f'Cumulative metered GPU-hours. Snapshot {r["as_of"]}.</text>')
    p.append("</svg>")
    return "\n".join(p)


def stack_strip(theme):
    """Chips in the same language as the figures, so nothing on the page is a
    third-party badge. Static: there is nothing here worth animating."""
    t = THEMES[theme]
    pad, gap, h, size = 13, 8, 30, 13
    xs, chips = 1, []
    for label in STACK:
        w = round(len(label) * size * 0.60) + pad * 2
        chips.append((xs, w, label))
        xs += w + gap
    W, H = xs - gap + 2, h + 2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
           f'height="{H}" role="img" aria-label="Stack: {", ".join(STACK)}">',
           f'<style>.m{{font-family:{MONO}}}</style>']
    for x, w, label in chips:
        out.append(f'<rect x="{x}" y="1" width="{w}" height="{h}" rx="7" fill="none" '
                   f'stroke="{t["rule"]}"/>'
                   f'<text class="m" x="{x + w/2:.1f}" y="{h/2 + 5.5:.0f}" font-size="{size}" '
                   f'text-anchor="middle" fill="{t["muted"]}">{label}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    contrib = json.loads((ROOT / "data" / "contributions.json").read_text())
    reclaim = json.loads((ROOT / "data" / "reclaim.json").read_text())
    total = 0
    for theme in THEMES:
        for name, svg in (("title", title_card(theme, contrib)),
                          ("compute", compute_figure(theme, reclaim)),
                          ("stack", stack_strip(theme))):
            p = ROOT / "assets" / f"{name}-{theme}.svg"
            p.write_text(svg)
            total += p.stat().st_size
            print(f"{p.name:22} {p.stat().st_size/1024:6.1f} KB")
    print(f"{'vector total':22} {total/1024:6.1f} KB")


if __name__ == "__main__":
    main()
