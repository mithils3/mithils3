#!/usr/bin/env python3
"""Render the profile header SVGs from live GitHub contribution data."""
import json, os, subprocess, sys, urllib.request
from datetime import date
from pathlib import Path

USER = "mithils3"
NAME = "Mithil Salunkhe"
TAGLINE = "CS @ Illinois  ·  agent evaluation, ML systems, HPC"
ROOT = Path(__file__).resolve().parent.parent

QUERY = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionLevel weekday } }
      }
    }
  }
}
"""

THEMES = {
    "dark": dict(
        panel_a="#0d1117", panel_b="#161b22", border="#30363d",
        ink="#e6edf3", muted="#8b949e", faint="#6e7681",
        empty="#1e242c",
        ramp=["#5c2a08", "#a34a00", "#e06a00", "#ff8c42"],
        glow="#ff5f05", glow_op="0.13",
    ),
    "light": dict(
        panel_a="#ffffff", panel_b="#f6f8fa", border="#d0d7de",
        ink="#1f2328", muted="#59636e", faint="#818b98",
        empty="#eaedf0",
        ramp=["#ffd0ad", "#ff9e57", "#f4700f", "#c93f00"],
        glow="#ff5f05", glow_op="0.10",
    ),
}

LEVELS = {
    "NONE": None, "FIRST_QUARTILE": 0, "SECOND_QUARTILE": 1,
    "THIRD_QUARTILE": 2, "FOURTH_QUARTILE": 3,
}

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

W, H = 1200, 356
PAD = 44
CELL, GAP = 17, 4
GRID_X, GRID_Y = PAD, 150


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if "errors" in body:
        sys.exit(f"graphql: {body['errors']}")
    return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def month_labels(weeks):
    out, last = [], None
    for i, wk in enumerate(weeks):
        d = date.fromisoformat(wk["contributionDays"][0]["date"])
        if d.month != last and i < len(weeks) - 1:
            out.append((i, d.strftime("%b")))
            last = d.month
    return [(i, m) for i, m in out if i == 0 or i > 1]


def render(cal, theme):
    t = THEMES[theme]
    weeks = cal["weeks"][-53:]
    total = f"{cal['totalContributions']:,}"
    grid_w = len(weeks) * (CELL + GAP) - GAP

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}" role="img" aria-label="{NAME}">']
    p.append(f"""<defs>
<linearGradient id="panel" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{t['panel_a']}"/><stop offset="1" stop-color="{t['panel_b']}"/>
</linearGradient>
<radialGradient id="glow" cx="0.88" cy="0.08" r="0.6">
<stop offset="0" stop-color="{t['glow']}" stop-opacity="{t['glow_op']}"/>
<stop offset="1" stop-color="{t['glow']}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{t['glow']}" stop-opacity="0.9"/>
<stop offset="1" stop-color="{t['glow']}" stop-opacity="0"/>
</linearGradient>
</defs>""")
    p.append(f"""<style>
.t{{font-family:{SANS}}}.m{{font-family:{MONO}}}
.cell{{opacity:0;animation:fadein .5s ease-out forwards}}
@keyframes fadein{{to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.cell{{animation:none;opacity:1}}}}
</style>""")
    p.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" '
             f'fill="url(#panel)" stroke="{t["border"]}"/>')
    p.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="13" fill="url(#glow)"/>')

    p.append(f'<text class="t" x="{PAD}" y="76" font-size="46" font-weight="700" '
             f'letter-spacing="-1.2" fill="{t["ink"]}">{NAME}</text>')
    p.append(f'<rect x="{PAD}" y="93" width="240" height="2" rx="1" fill="url(#rule)"/>')
    p.append(f'<text class="m" x="{PAD}" y="120" font-size="15.5" '
             f'fill="{t["muted"]}">{TAGLINE}</text>')
    p.append(f'<text class="m" x="{W-PAD}" y="76" font-size="30" font-weight="600" '
             f'text-anchor="end" fill="{t["ink"]}">{total}</text>')
    p.append(f'<text class="m" x="{W-PAD}" y="97" font-size="12.5" letter-spacing="0.6" '
             f'text-anchor="end" fill="{t["faint"]}">CONTRIBUTIONS · LAST 12 MONTHS</text>')

    for i, m in month_labels(weeks):
        p.append(f'<text class="m" x="{GRID_X + i*(CELL+GAP)}" y="{GRID_Y-9}" '
                 f'font-size="11.5" fill="{t["faint"]}">{m}</text>')

    for wi, wk in enumerate(weeks):
        for day in wk["contributionDays"]:
            lvl = LEVELS[day["contributionLevel"]]
            fill = t["empty"] if lvl is None else t["ramp"][lvl]
            x = GRID_X + wi * (CELL + GAP)
            y = GRID_Y + day["weekday"] * (CELL + GAP)
            delay = round(wi * 0.014, 3)
            p.append(f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                     f'rx="4" fill="{fill}" style="animation-delay:{delay}s"/>')

    legend_y = GRID_Y + 7 * (CELL + GAP) + 20
    p.append(f'<text class="m" x="{PAD}" y="{legend_y+9}" font-size="11.5" '
             f'fill="{t["faint"]}">Less</text>')
    lx = PAD + 34
    for fill in [t["empty"]] + t["ramp"]:
        p.append(f'<rect x="{lx}" y="{legend_y}" width="11" height="11" rx="3" fill="{fill}"/>')
        lx += 15
    p.append(f'<text class="m" x="{lx+2}" y="{legend_y+9}" font-size="11.5" '
             f'fill="{t["faint"]}">More</text>')
    p.append(f'<text class="m" x="{GRID_X+grid_w}" y="{legend_y+9}" font-size="11.5" '
             f'text-anchor="end" fill="{t["faint"]}">github.com/{USER}</text>')
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    cal = fetch()
    for theme in THEMES:
        out = ROOT / "assets" / f"header-{theme}.svg"
        out.write_text(render(cal, theme))
        print(out, out.stat().st_size, "bytes")
