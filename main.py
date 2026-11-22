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

import struct
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


def build_image(dest: Path) -> None:
    """BUILDER: author this in-session. Draw the picture procedurally
    (stdlib only, deterministic — no clock, no unseeded randomness, no
    network) or write a sibling image generated in-session to dest.
    This placeholder must not survive into any submitted commit."""
    raise NotImplementedError("BUILDER: author build_image() in-session")


def main() -> None:
    dest_dir = output_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "entry.png"
    build_image(dest)
    check_png(dest)


if __name__ == "__main__":
    main()
