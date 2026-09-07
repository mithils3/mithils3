#!/usr/bin/env python3
"""Render the three.js contribution skyline.

Default is a single high-quality still. --frames N renders an orbiting loop
instead, which costs roughly 35x the bytes for motion nobody watches twice;
the still is what the README ships.
"""
import argparse, functools, http.server, shutil, socketserver, subprocess, tempfile, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
GL = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]


def serve(root):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=1)
    ap.add_argument("--width", type=int, default=2000)
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--quality", type=int, default=86)
    ap.add_argument("--out", default="assets/skyline.webp")
    args = ap.parse_args()

    srv, port = serve(ROOT)
    tmp = Path(tempfile.mkdtemp(prefix="skyline-"))
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=GL)
            pg = b.new_page(viewport={"width": 2000, "height": 620})
            pg.goto(f"http://127.0.0.1:{port}/scenes/skyline.html")
            pg.wait_for_function("window.SCENE_READY === true", timeout=120_000)
            crop = pg.evaluate("window.CROP")
            for i in range(args.frames):
                # a lone still sits at the midpoint of the sweep
                pg.evaluate("([i, n]) => window.setFrame(i, n)",
                            [i, args.frames] if args.frames > 1 else [1, 3])
                pg.screenshot(path=str(tmp / f"f{i:03d}.png"), omit_background=True, clip=crop)
            b.close()

        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        scale = f"scale={args.width}:-2:flags=lanczos"
        if args.frames == 1:
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp / "f000.png"),
                   "-vf", scale, "-lossless", "0", "-quality", str(args.quality), str(out)]
            frames = 1
        else:
            # ping-pong so the loop is seamless
            n = args.frames
            for j, i in enumerate(range(n - 2, 0, -1)):
                shutil.copy(tmp / f"f{i:03d}.png", tmp / f"f{n + j:03d}.png")
            frames = 2 * n - 2
            cmd = ["ffmpeg", "-y", "-loglevel", "error",
                   "-framerate", str(args.fps), "-i", str(tmp / "f%03d.png"), "-vf", scale,
                   "-loop", "0", "-lossless", "0", "-quality", str(args.quality),
                   "-compression_level", "6", "-pix_fmt", "yuva420p", str(out)]
        subprocess.run(cmd, check=True)
        print(out, f"{out.stat().st_size / 1024:.0f} KB", f"{frames} frame(s)",
              f"{crop['width']}x{crop['height']} source")
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
