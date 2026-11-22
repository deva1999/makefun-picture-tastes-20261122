"""main.py — writes one food/drink picture to /output/entry.png.

Contract (from the competition requirements): /output/entry.png is a whole
PNG or JPEG of at most 1,048,576 bytes and 1024 by 1024 pixels; the program
runs in a sandbox with no network; two runs must produce identical output.

The picture itself is authored in-session by the builder — either drawn
procedurally here with the standard library only, or generated in-session
and saved beside this file. This stub holds no picture: BUILDER replaces
build_image() in-session (that replacement + the revise edit are the
authored lines the transcript gate counts — keep authored share >= 40%).
"""

import math
import random
import struct
import zlib
from pathlib import Path

MAX_BYTES = 1_048_576
MAX_DIM = 1024


def output_dir() -> Path:
    """Where the grader wants the image: /output, or MAKEFUN_OUTPUT_DIR."""
    override = __import__("os").environ.get("MAKEFUN_OUTPUT_DIR")
    if override:
        return Path(override)
    system_out = Path("/output")
    try:
        system_out.mkdir(parents=True, exist_ok=True)
        if __import__("os").access(system_out, __import__("os").W_OK):
            return system_out
    except OSError:
        pass
    return Path(__file__).resolve().parent / "output"


def check_png(path: Path) -> None:
    """Fail loudly unless path is a valid PNG within the size limits."""
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{path} is {len(data)} bytes, over {MAX_BYTES}")
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit(f"{path} is not a PNG (bad signature)")
    width, height = struct.unpack(">II", data[16:24])
    if width > MAX_DIM or height > MAX_DIM:
        raise SystemExit(f"{path} is {width}x{height}, over {MAX_DIM}x{MAX_DIM}")


# ---------------------------------------------------------------------------
# Procedural ramen picture — authored in-session, stdlib only, deterministic.
# One bowl of steaming ramen fills ~90% of the frame on a plain dark
# background: glossy broth, chopsticks lifting noodles, halved egg, green
# onions, chashu, narutomaki. No text anywhere in the image.
# ---------------------------------------------------------------------------

W = H = 1024


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rows = [bytearray(w * 3) for _ in range(h)]

    def px(self, x, y, r, g, b, a=1.0):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = x * 3
            row = self.rows[y]
            if a >= 1.0:
                row[i], row[i + 1], row[i + 2] = r, g, b
            else:
                row[i] = int(row[i] * (1 - a) + r * a)
                row[i + 1] = int(row[i + 1] * (1 - a) + g * a)
                row[i + 2] = int(row[i + 2] * (1 - a) + b * a)

    def hspan(self, x0, x1, y, r, g, b, a=1.0):
        """Fill one horizontal run (clamped)."""
        if not (0 <= y < self.h):
            return
        x0 = max(0, int(x0))
        x1 = min(self.w - 1, int(x1))
        if x1 < x0:
            return
        row = self.rows[y]
        if a >= 1.0:
            for x in range(x0, x1 + 1):
                i = x * 3
                row[i], row[i + 1], row[i + 2] = r, g, b
        else:
            for x in range(x0, x1 + 1):
                i = x * 3
                row[i] = int(row[i] * (1 - a) + r * a)
                row[i + 1] = int(row[i + 1] * (1 - a) + g * a)
                row[i + 2] = int(row[i + 2] * (1 - a) + b * a)

    def disc(self, cx, cy, rad, r, g, b, a=1.0):
        rad = int(rad)
        for y in range(cy - rad, cy + rad + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0, rad * rad - dy * dy)))
            self.hspan(cx - dx, cx + dx, y, r, g, b, a)

    def ellipse(self, cx, cy, rx, ry, r, g, b, a=1.0):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            t = (y - cy) / ry
            if abs(t) >= 1:
                continue
            dx = int(rx * math.sqrt(1 - t * t))
            self.hspan(cx - dx, cx + dx, y, r, g, b, a)

    def ellipse_grad(self, cx, cy, rx, ry, top, bot, a=1.0):
        """Vertical-gradient filled ellipse."""
        for y in range(int(cy - ry), int(cy + ry) + 1):
            t = (y - cy) / ry
            if abs(t) >= 1:
                continue
            f = (t + 1) / 2
            r = int(top[0] + (bot[0] - top[0]) * f)
            g = int(top[1] + (bot[1] - top[1]) * f)
            b = int(top[2] + (bot[2] - top[2]) * f)
            dx = int(rx * math.sqrt(1 - t * t))
            self.hspan(cx - dx, cx + dx, y, r, g, b, a)

    def thick_line(self, x0, y0, x1, y1, width, r, g, b, a=1.0):
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.5) + 1
        for s in range(steps + 1):
            f = s / steps
            x = int(x0 + (x1 - x0) * f)
            y = int(y0 + (y1 - y0) * f)
            self.disc(x, y, max(1, int(width / 2)), r, g, b, a)

    def wavy(self, x0, y0, x1, y1, amp, freq, phase, width, r, g, b, a=1.0):
        """A sine-wavy strand from (x0,y0) to (x1,y1)."""
        steps = int(math.hypot(x1 - x0, y1 - y0) / 4) + 8
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length, dx / length
        for s in range(steps + 1):
            f = s / steps
            off = amp * math.sin(f * freq * math.tau + phase)
            x = int(x0 + dx * f + nx * off)
            y = int(y0 + dy * f + ny * off)
            self.disc(x, y, max(1, int(width / 2)), r, g, b, a)


def _lerp(c0, c1, f):
    return tuple(int(c0[i] + (c1[i] - c0[i]) * f) for i in range(3))


def build_image(dest: Path) -> None:
    rng = random.Random(20261122)  # fixed seed: identical output every run
    cv = Canvas(W, H)

    # --- 1. Plain dark background with a warm radial glow behind the bowl.
    for y in range(H):
        # vertical falloff: slightly lighter near the bowl, near-black edges
        f = abs(y - 560) / 560
        base = _lerp((52, 32, 20), (14, 9, 7), min(1.0, f * 1.15))
        row = cv.rows[y]
        for x in range(W):
            d = math.hypot(x - 512, (y - 560) * 1.15) / 700
            glow = max(0.0, 1.0 - d) ** 2 * 0.55
            row[x * 3] = min(255, int(base[0] + 62 * glow))
            row[x * 3 + 1] = min(255, int(base[1] + 34 * glow))
            row[x * 3 + 2] = min(255, int(base[2] + 14 * glow))

    # soft contact shadow under the bowl
    cv.ellipse(512, 958, 420, 42, 0, 0, 0, 0.45)
    cv.ellipse(512, 950, 360, 30, 0, 0, 0, 0.35)

    # --- 2. Bowl body: deep lacquer red, darker toward the foot.
    cv.ellipse_grad(512, 640, 432, 330, (146, 38, 24), (58, 14, 10))
    # bowl foot
    cv.ellipse(512, 940, 190, 34, 40, 10, 8)
    cv.ellipse(512, 934, 190, 30, 74, 20, 13)
    # rim: dark outer ring + bright lacquer edge catching the light
    cv.ellipse(512, 545, 432, 118, 96, 20, 12)
    cv.ellipse(512, 545, 414, 108, 176, 58, 30)
    # rim highlight arc (upper-left light)
    for deg in range(195, 345, 2):
        a = math.radians(deg)
        cv.disc(int(512 + 420 * math.cos(a)), int(545 + 112 * math.sin(a)),
                5, 255, 150, 100, 0.55)
    # glossy vertical sheen on the bowl's left flank
    for k in range(26):
        y = 640 + k * 10
        t = k / 25
        cv.hspan(150 + 60 * t, 205 + 40 * t, y, 255, 120, 70, 0.10 * (1 - t))

    # --- 3. Broth: glossy amber surface with a warm gradient + oil sheen.
    cv.ellipse_grad(512, 545, 398, 100, (244, 178, 84), (196, 116, 30))
    # darker broth ring near the rim for depth
    for k in range(10):
        cv.ellipse(512, 545, 398 - k * 3, 100 - k, 210, 128, 34, 0.10)
    # broth swirl arcs (light catching the surface)
    for cx, cy, rad, a0, a1 in [(470, 545, 150, 200, 330), (560, 560, 120, 20, 160),
                                (512, 545, 210, 300, 60), (430, 530, 90, 180, 320)]:
        for deg in range(a0, a1, 3):
            a = math.radians(deg)
            cv.disc(int(cx + rad * math.cos(a)), int(cy + rad * 0.42 * math.sin(a)),
                    4, 255, 214, 130, 0.35)
    # golden oil droplets: glossy beads on the broth
    for _ in range(26):
        x = int(rng.uniform(180, 844))
        y = int(545 + rng.uniform(-78, 78) * 0.9)
        r = int(rng.uniform(4, 11))
        cv.disc(x, y, r, 247, 193, 78, 0.85)
        cv.disc(x - r // 3, y - r // 3, max(1, r // 3), 255, 240, 190, 0.9)

    # --- 4. Chashu: two rolled pork slices (pink with a brown spiral).
    for cx, cy, rad in [(668, 585, 78), (742, 545, 62)]:
        cv.disc(cx, cy, rad, 178, 96, 58)
        cv.disc(cx, cy, rad - 8, 232, 176, 138)
        for turn in range(3):
            rr = rad - 18 - turn * 14
            if rr <= 6:
                break
            for deg in range(0, 300, 4):
                a = math.radians(deg + turn * 40)
                cv.disc(int(cx + rr * math.cos(a)), int(cy + rr * 0.8 * math.sin(a)),
                        4, 176, 106, 66, 0.9)
        cv.disc(cx - rad // 3, cy - rad // 3, 10, 255, 220, 180, 0.5)

    # --- 5. Halved egg: bright white, deep-orange jammy yolk.
    cv.ellipse(318, 540, 92, 66, 253, 246, 233)
    cv.ellipse(318, 540, 84, 59, 250, 240, 222)
    cv.disc(318, 542, 42, 232, 128, 8)
    cv.disc(318, 542, 34, 246, 154, 26)
    cv.disc(306, 530, 10, 255, 196, 90, 0.85)  # yolk gloss

    # --- 6. Narutomaki: white fish-cake disc with a pink spiral.
    cv.disc(448, 612, 44, 255, 250, 244)
    for deg in range(0, 540, 4):
        a = math.radians(deg)
        rr = 6 + deg * 0.055
        cv.disc(int(448 + rr * math.cos(a)), int(612 + rr * 0.85 * math.sin(a)),
                4, 232, 122, 154, 0.95)
    cv.disc(448, 612, 6, 232, 122, 154)

    # --- 7. Noodle mound: tangled glossy strands filling the broth centre.
    noodle_dark = (214, 164, 74)
    noodle_mid = (246, 214, 138)
    noodle_hi = (255, 243, 196)
    for i in range(46):
        x0 = int(rng.uniform(330, 700))
        y0 = int(rng.uniform(500, 590))
        ang = rng.uniform(-0.6, 0.6) + (math.pi if rng.random() < 0.5 else 0)
        ln = rng.uniform(70, 170)
        x1 = int(x0 + math.cos(ang) * ln)
        y1 = int(y0 + math.sin(ang) * ln * 0.45)
        w = rng.uniform(5, 8)
        cv.wavy(x0, y0, x1, y1, rng.uniform(6, 16), rng.uniform(2.2, 4.0),
                rng.uniform(0, 6.28), w + 2, *noodle_dark, 0.9)
        cv.wavy(x0, y0, x1, y1, rng.uniform(6, 16), rng.uniform(2.2, 4.0),
                rng.uniform(0, 6.28), w, *noodle_mid, 0.95)
        cv.wavy(x0, y0 - 2, x1, y1 - 2, rng.uniform(6, 16), rng.uniform(2.2, 4.0),
                rng.uniform(0, 6.28), 2, *noodle_hi, 0.7)

    # --- 8. Chopsticks lifting a glossy bundle of noodles.
    # sticks: warm wood, upper-right to the lifted bundle
    cv.thick_line(742, 128, 556, 428, 15, 122, 78, 34)
    cv.thick_line(776, 168, 588, 448, 15, 110, 68, 28)
    cv.thick_line(742, 128, 556, 428, 6, 178, 124, 62, 0.8)
    cv.thick_line(776, 168, 588, 448, 6, 164, 110, 54, 0.8)
    # lifted bundle: strands draped from the chopstick tips, hanging to broth
    for i in range(16):
        sway = rng.uniform(-26, 26)
        top_x = 560 + i * 2 + int(sway * 0.4)
        top_y = 430 + (i % 3) * 4
        bot_x = 520 + i * 5 + int(sway)
        bot_y = 560 + (i % 4) * 6
        cv.wavy(top_x, top_y, bot_x, bot_y, 14, 1.6, i * 0.9, 7, *noodle_dark, 0.95)
        cv.wavy(top_x, top_y, bot_x, bot_y, 14, 1.6, i * 0.9, 5, *noodle_mid, 0.95)
        cv.wavy(top_x, top_y - 2, bot_x, bot_y - 2, 14, 1.6, i * 0.9, 2, *noodle_hi, 0.8)
    # noodle loop caught between the sticks
    for k in range(9):
        cv.wavy(548 + k * 3, 428, 600 + k * 2, 470, 10, 2.0, k, 5, *noodle_mid, 0.95)

    # --- 9. Green onions: crisp rings + chopped bits scattered on the broth.
    for _ in range(34):
        x = int(rng.uniform(200, 830))
        y = int(545 + rng.uniform(-80, 80) * 0.85)
        if (x - 318) ** 2 / 92 ** 2 + (y - 540) ** 2 / 66 ** 2 < 1.1:
            continue  # keep the egg clean
        r = int(rng.uniform(5, 10))
        cv.disc(x, y, r, 46, 140, 62)
        cv.disc(x, y, max(2, r - 3), 126, 208, 122)
        cv.disc(x, y, max(1, r - 5), 30, 90, 40)
    for _ in range(12):
        x = int(rng.uniform(240, 800))
        y = int(545 + rng.uniform(-70, 70))
        cv.disc(x, y, 3, 90, 190, 90, 0.9)

    # --- 10. Steam: soft white wisps rising from the hot broth.
    # REVISED: stronger steam (higher alpha, wider cores) so the heat reads
    # at small size, plus a brighter gloss streak on the lifted noodles.
    for bx, drift, height in [(400, -24, 300), (512, 6, 340), (624, 26, 300),
                              (470, -40, 250), (570, 40, 250)]:
        for pass_no in range(4):
            for s in range(60):
                f = s / 59
                y = int(480 - f * height)
                x = int(bx + drift * f + 20 * math.sin(f * 9 + pass_no * 1.7)
                        + rng.uniform(-3, 3))
                rad = int(12 + f * 18 + pass_no * 3)
                cv.disc(x, y, rad, 255, 250, 244, 0.065)
    # bright steam cores (thin, so the wisps read at small size)
    for bx, drift, height in [(400, -24, 300), (512, 6, 340), (624, 26, 300)]:
        for s in range(50):
            f = s / 49
            y = int(480 - f * height)
            x = int(bx + drift * f + 20 * math.sin(f * 9))
            cv.disc(x, y, 6, 255, 255, 255, 0.24)

    # --- 11. Final gloss: re-draw the chopsticks OVER the steam so the
    # lift reads clearly, then specular streaks on broth + rim catch-light.
    cv.thick_line(742, 128, 556, 428, 15, 132, 86, 38)
    cv.thick_line(776, 168, 588, 448, 15, 120, 76, 32)
    cv.thick_line(742, 128, 556, 428, 6, 190, 134, 68, 0.9)
    cv.thick_line(776, 168, 588, 448, 6, 176, 120, 60, 0.9)
    for i in range(6):
        cv.wavy(556 + i * 3, 428 + (i % 3) * 4, 530 + i * 5, 556, 12, 1.6,
                i * 0.9, 5, *noodle_mid, 0.95)
    for deg in range(205, 285, 3):
        a = math.radians(deg)
        cv.disc(int(512 + 380 * math.cos(a)), int(545 + 96 * math.sin(a)),
                4, 255, 220, 160, 0.5)
    cv.wavy(240, 500, 420, 480, 8, 1.2, 0.4, 6, 255, 230, 170, 0.35)
    cv.wavy(600, 610, 800, 590, 8, 1.2, 2.0, 6, 255, 230, 170, 0.30)

    # --- Encode PNG (stdlib zlib, filter 0, deterministic).
    raw = b"".join(b"\x00" + bytes(row) for row in cv.rows)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)

    def chunk(tag, payload):
        c = struct.pack(">I", len(payload)) + tag + payload
        return c + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 6))
           + chunk(b"IEND", b""))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(png)


def main() -> None:
    dest_dir = output_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "entry.png"
    build_image(dest)
    check_png(dest)


if __name__ == "__main__":
    main()
