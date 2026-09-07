#!/usr/bin/env python3
"""Project the contribution year as an axonometric city and emit it as SVG.

No rasteriser is involved. Each day is a box, each box is three flat-shaded
quads, and the whole scene is depth-sorted and written as vector paths, so it
is exact at any zoom and on any display. The week axis is horizontal, so the
ground line and the month scale are straight.

The month-by-month build is CSS on twelve groups.
"""
import json
from math import log1p
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

W_STEP = 17.2           # px per week, horizontal
D_X, D_Y = 10.4, 8.2    # px per weekday, toward the viewer
FILL = 0.78             # box footprint inside its cell
MAXH = 76.0             # px at the busiest day
BASE = 3.0              # px for a day with nothing on it
PAD = 22.0            # top and sides; the month scale sets the bottom

# top / front / right. A single light from the upper left, baked per face,
# which is all a flat-shaded fragment shader would have done anyway. The dark
# theme can take a steeper falloff before the sides go to mud.

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

THEMES = {
    "dark": dict(ramp=["#116634", "#188f45", "#28bd5b", "#56e883"],
                 empty="#2b323d", ink="#e6edf3", muted="#8b939f", faint="#6b7480",
                 shadow="#000000", shadow_op=0.30,
                 face={"top": 1.00, "front": 0.80, "right": 0.585}),
    "light": dict(ramp=["#b4e8c1", "#5cc775", "#2c9c4e", "#106b31"],
                  empty="#dfe3e8", ink="#1f2328", muted="#59636e", faint="#818b98",
                  shadow="#243044", shadow_op=0.13,
                  face={"top": 1.00, "front": 0.87, "right": 0.72}),
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def hex_to_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def shade(hexcol, k):
    r, g, b = hex_to_rgb(hexcol)
    f = lambda v: max(0, min(255, round(v * k)))
    return f"#{f(r):02x}{f(g):02x}{f(b):02x}"


def ramp_at(ramp, t):
    x = min(0.9999, max(0.0, t)) * (len(ramp) - 1)
    i = int(x)
    a, b = hex_to_rgb(ramp[i]), hex_to_rgb(ramp[min(i + 1, len(ramp) - 1)])
    f = x - i
    return "#" + "".join(f"{round(a[k] + (b[k] - a[k]) * f):02x}" for k in range(3))


def quad(p):
    return "M" + " ".join(f"{x:.1f} {y:.1f}" for x, y in p) + "Z"


def build(theme, cal):
    t = THEMES[theme]
    weeks = cal["weeks"]
    counts = sorted(d["contributionCount"] for w in weeks for d in w if d["contributionCount"])
    # near-linear against p95. The tail is heavy (median 6, max 139), so a
    # log scale flattens every ordinary day into the same tower
    cap = counts[min(len(counts) - 1, int(len(counts) * 0.95))] if counts else 1
    peak = max((d for w in weeks for d in w), key=lambda d: d["contributionCount"])

    keys = sorted({d["date"][:7] for w in weeks for d in w})
    cells = []
    for wi, week in enumerate(weeks):
        for d in week:
            c = d["contributionCount"]
            frac = min(1.0, c / cap) ** 0.9 if c else 0.0
            # a soft knee above the cap, so the busiest day of the year is
            # visibly the tallest instead of clipping flat with its neighbours
            hf = frac if c <= cap else 1.0 + 0.36 * log1p((c - cap) / cap)
            cells.append(dict(
                w=wi, d=d["weekday"], count=c, date=d["date"],
                h=BASE + MAXH * hf if c else BASE,
                col=ramp_at(t["ramp"], frac) if c else t["empty"],
                mi=keys.index(d["date"][:7]),
            ))

    ox = lambda c: c["w"] * W_STEP + c["d"] * D_X
    oy = lambda c: c["d"] * D_Y
    ax, ay = FILL * W_STEP, 0.0
    bx, by = FILL * D_X, FILL * D_Y

    xs = [ox(c) for c in cells] + [ox(c) + ax + bx for c in cells]
    ys = [oy(c) + by for c in cells] + [oy(c) - c["h"] for c in cells]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    LABEL = 40.0          # ground line to the bottom edge, month scale included
    W = maxx - minx + 2 * PAD
    H = maxy - miny + PAD + LABEL
    sx = lambda v: v - minx + PAD
    sy = lambda v: v - miny + PAD

    # painter's order: the projection's view vector has a negative week
    # component, so within a row the left-hand box is nearer and paints last
    order = sorted(cells, key=lambda c: c["d"] - (D_X / W_STEP) * c["w"])

    groups = {i: [] for i in range(len(keys))}
    shadows = []
    for c in order:
        X, Y, h = sx(ox(c)), sy(oy(c)), c["h"]
        top = [(X, Y - h), (X + ax, Y + ay - h), (X + ax + bx, Y + ay + by - h), (X + bx, Y + by - h)]
        front = [(X + bx, Y + by), (X + ax + bx, Y + ay + by),
                 (X + ax + bx, Y + ay + by - h), (X + bx, Y + by - h)]
        right = [(X + ax, Y + ay), (X + ax + bx, Y + ay + by),
                 (X + ax + bx, Y + ay + by - h), (X + ax, Y + ay - h)]
        g = groups[c["mi"]]
        if c["count"]:
            g.append(f'<path d="{quad(front)}" fill="{shade(c["col"], t["face"]["front"])}"/>')
            g.append(f'<path d="{quad(right)}" fill="{shade(c["col"], t["face"]["right"])}"/>')
            g.append(f'<path d="{quad(top)}" fill="{shade(c["col"], t["face"]["top"])}"/>')
        else:
            # a day with nothing on it is 3px tall; one quad reads the same and
            # keeps a third of the scene's paths out of the document
            g.append(f'<path d="{quad(top)}" fill="{c["col"]}"/>')
        if c["count"]:
            k = 0.26 * h
            shadows.append(quad([(X + k, Y + k * 0.42), (X + ax + k, Y + ay + k * 0.42),
                                 (X + ax + bx + k, Y + ay + by + k * 0.42),
                                 (X + bx + k, Y + by + k * 0.42)]))

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" '
         f'height="{H:.0f}" role="img" aria-label="{cal["total"]:,} contributions over the last '
         f'twelve months, one tower per day. Busiest day {peak["date"]} with '
         f'{peak["contributionCount"]} commits.">']
    # An explicit numeric origin per group. transform-box:fill-box would make
    # Chrome recompute a bounding box over every path in the group on every
    # frame, which is what made the build stutter.
    p.append(f"""<style>
.m{{font-family:{MONO}}}
.mo{{animation:rise 1.35s cubic-bezier(.16,.72,.24,1) var(--d) backwards}}
@keyframes rise{{from{{transform:scaleY(.015)}}}}
.lb{{animation:app 1.1s ease-out var(--d) backwards}}
@keyframes app{{from{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.mo,.lb{{animation:none}}}}
</style>""")
    # one path, nonzero fill, so overlapping shadows stay a single flat tone
    p.append(f'<path d="{" ".join(shadows)}" fill="{t["shadow"]}" '
             f'fill-opacity="{t["shadow_op"]}"/>')

    beat = 0.34
    for mi, key in enumerate(keys):
        mcells = [c for c in cells if c["mi"] == mi]
        gx = sum(sx(ox(c)) for c in mcells) / len(mcells)
        gy = max(sy(oy(c)) + by for c in mcells)
        p.append(f'<g class="mo" style="--d:{mi*beat:.2f}s;'
                 f'transform-origin:{gx:.0f}px {gy:.0f}px">'
                 + "".join(groups[mi]) + "</g>")

    # month scale on the straight front edge
    base_y = sy(max(oy(c) + by for c in cells)) + 27
    for mi, key in enumerate(keys):
        first = min((c for c in cells if c["mi"] == mi), key=lambda c: c["w"])
        x = sx(ox(first))
        p.append(f'<g class="lb" style="--d:{mi*beat:.3f}s">'
                 f'<rect x="{x:.1f}" y="{base_y-11:.1f}" width="1" height="7" '
                 f'fill="{t["faint"]}" fill-opacity=".65"/>'
                 f'<text class="m" x="{x:.1f}" y="{base_y:.1f}" font-size="10.5" '
                 f'fill="{t["muted"]}">{MONTHS[int(key[5:7])-1]}</text></g>')

    pc = next(c for c in cells if c["date"] == peak["date"])
    px_ = sx(ox(pc)) + (ax + bx) / 2
    py_ = sy(oy(pc)) + (ay + by) / 2 - pc["h"]
    p.append(f'<g class="lb" style="--d:{pc["mi"]*beat:.3f}s">'
             f'<rect x="{px_:.1f}" y="{py_-26:.1f}" width="1" height="20" '
             f'fill="{t["faint"]}" fill-opacity=".8"/>'
             f'<text class="m" x="{px_-6:.1f}" y="{py_-42:.1f}" font-size="12.5" '
             f'font-weight="600" text-anchor="end" fill="{t["ink"]}">'
             f'{peak["contributionCount"]} commits</text>'
             f'<text class="m" x="{px_-6:.1f}" y="{py_-30:.1f}" font-size="10.5" '
             f'text-anchor="end" fill="{t["faint"]}">{pretty(peak["date"])}</text></g>')
    p.append("</svg>")
    return "\n".join(p)


def pretty(iso):
    y, m, d = iso.split("-")
    return f"{MONTHS[int(m)-1]} {int(d)}, {y}"


def main():
    cal = json.loads((ROOT / "data" / "contributions.json").read_text())
    for theme in THEMES:
        out = ROOT / "assets" / f"skyline-{theme}.svg"
        out.write_text(build(theme, cal))
        print(f"{out.name:22} {out.stat().st_size/1024:6.1f} KB")


if __name__ == "__main__":
    main()
