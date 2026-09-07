#!/usr/bin/env python3
"""Render the three.js contribution skyline as a month-by-month build.

The camera is fixed and only the towers move, so consecutive frames differ
in a small band of pixels and the WebP animation encoder can delta them.
Frames are rendered at 2x device pixels and downsampled, which is what makes
the towers hold up on a retina display.
"""
import argparse, functools, http.server, shutil, socketserver, tempfile, threading, time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
GL = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]


def serve(root):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    handler_quiet = type("Q", (handler.func,), {"log_message": lambda *a: None})
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(handler_quiet, **handler.keywords))
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


# Neutral ink that holds up on both the light and the dark GitHub canvas,
# since the frame is transparent and sits on whichever one the reader has.
INK = (139, 147, 161)
INK_STRONG = (168, 176, 189)
ACCENT = (240, 128, 12)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def _font(path, px):
    try:
        return ImageFont.truetype(path, px)
    except OSError:
        return ImageFont.load_default()


def annotate(img, anchors, crop, w, h, display, t):
    """Draw the month scale and the peak-day callout onto one frame.

    Labels arrive with their own month, so the build names the year as it
    rises instead of moving for its own sake.
    """
    k = w / display                      # source px per displayed px
    d = ImageDraw.Draw(img, "RGBA")
    to_x = lambda v: (v - crop["x"]) * w / crop["width"]
    to_y = lambda v: (v - crop["y"]) * h / crop["height"]
    fade = lambda a: max(0.0, min(1.0, (t - a["start"]) / a["dur"]))

    f_month = _font(FONT, round(10.5 * k))
    f_peak = _font(FONT_B, round(11 * k))
    f_note = _font(FONT, round(9.5 * k))

    for a in anchors["months"]:
        alpha = fade(a)
        if alpha <= 0.02:
            continue
        x, y = to_x(a["x"]), to_y(a["y"])
        d.line([(x, y + 5 * k), (x, y + 12 * k)], fill=INK + (round(90 * alpha),),
               width=max(1, round(k)))
        label = _MONTHS[int(a["key"][5:7]) - 1]
        d.text((x, y + 16 * k), label, font=f_month, fill=INK + (round(235 * alpha),))

    p = anchors["peak"]
    alpha = fade(p)
    if alpha > 0.02:
        x, y = to_x(p["x"]), to_y(p["y"])
        rise = 30 * k
        d.line([(x, y - 6 * k), (x, y - rise)], fill=INK + (round(120 * alpha),),
               width=max(1, round(k)))
        r = 3 * k
        d.ellipse([x - r, y - 6 * k - r, x + r, y - 6 * k + r],
                  fill=ACCENT + (round(255 * alpha),))
        d.text((x - 4 * k, y - rise - 15 * k), f"{p['count']} commits", font=f_peak,
               anchor="rs", fill=INK_STRONG + (round(245 * alpha),))
        d.text((x - 4 * k, y - rise - 2 * k), _pretty(p["date"]), font=f_note,
               anchor="rs", fill=INK + (round(190 * alpha),))


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _pretty(iso):
    y, m, dd = iso.split("-")
    return f"{_MONTHS[int(m)-1]} {int(dd)}, {y}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=64, help="frames in the build")
    ap.add_argument("--width", type=int, default=2600, help="output width in px")
    ap.add_argument("--scale", type=int, default=2, help="device pixel ratio to render at")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--hold", type=float, default=4.5, help="seconds resting on the finished city")
    ap.add_argument("--quality", type=int, default=76)
    ap.add_argument("--still", action="store_true", help="one frame, no animation")
    ap.add_argument("--display", type=int, default=846,
                    help="width the image is shown at, which sets label size")
    ap.add_argument("--dump", help="also write the annotated frames as PNGs here")
    ap.add_argument("--out", default="assets/skyline.webp")
    args = ap.parse_args()

    srv, port = serve(ROOT)
    tmp = Path(tempfile.mkdtemp(prefix="skyline-"))
    t0 = time.time()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=GL)
            pg = b.new_page(viewport={"width": 2000, "height": 620},
                            device_scale_factor=args.scale)
            pg.goto(f"http://127.0.0.1:{port}/scenes/skyline.html")
            pg.wait_for_function("window.SCENE_READY === true", timeout=180_000)
            crop = pg.evaluate("window.CROP")
            months = pg.evaluate("window.MONTHS")
            anchors = pg.evaluate("window.ANCHORS")
            # room under the front edge for the month scale
            crop["height"] = min(620 - crop["y"], crop["height"] + 46)
            n = 1 if args.still else args.frames
            for i in range(n):
                pg.evaluate("t => window.setBuild(t)", 1.0 if args.still else i / (n - 1))
                pg.screenshot(path=str(tmp / f"f{i:03d}.png"), omit_background=True, clip=crop)
            b.close()

        raw = [Image.open(tmp / f"f{i:03d}.png").convert("RGBA") for i in range(n)]
        w = args.width
        h = round(raw[0].height * w / raw[0].width / 2) * 2
        frames = []
        for i, im in enumerate(raw):
            f = im.resize((w, h), Image.LANCZOS)
            annotate(f, anchors, crop, w, h, args.display,
                     1.0 if args.still or n == 1 else i / (n - 1))
            frames.append(f)

        if args.dump:
            dd = Path(args.dump); dd.mkdir(parents=True, exist_ok=True)
            for i, f in enumerate(frames):
                f.save(dd / f"a{i:03d}.png")

        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        if args.still:
            frames[0].save(out, quality=88, method=6)
        else:
            step = round(1000 / args.fps)
            # a fast reverse teardown, subsampled, so the loop restarts without a cut
            tail = frames[::-5][1:]
            durations = ([step] * len(frames) + [round(args.hold * 1000)]
                         + [round(step * 0.6)] * len(tail))
            frames[0].save(
                out, save_all=True, append_images=frames[1:] + [frames[-1]] + tail,
                duration=durations, loop=0, quality=args.quality, method=6,
                minimize_size=True, allow_mixed=True,
            )
        total = 1 if args.still else len(frames) + 1 + len(tail)
        print(f"{out}  {out.stat().st_size/1024:.0f} KB  {total} frames  "
              f"{w}x{h} out  {crop['width']*args.scale}x{crop['height']*args.scale} rendered  "
              f"{months} months  {time.time()-t0:.0f}s")
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
