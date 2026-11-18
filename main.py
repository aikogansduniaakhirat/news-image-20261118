#!/usr/bin/env python3
"""make.fun entry for news-image-20261118.

The bounty asks for one image that sums up the world's news of Wednesday
18 November 2026, written to /output/entry.png by a program that runs with no
network access. The rules allow the simplest form of entry: a repository that
holds the image plus a program that copies it to the output directory. That is
exactly what this is, and nothing more is needed.

    MAKEFUN_OUTPUT_DIR=out python3 main.py

The image itself is art/entry.png, rendered at build time by
art/render_image.py (Pillow, no network -- see art/README.md for the layout and
the checks it passed before it was committed). Rendering never happens here, so
this program is standard-library only, touches no socket, and writes
byte-identical output on every run: copying the same file twice yields the same
bytes, which is what the two-run reproducibility gate wants.

Guard rails, because a malformed image scores zero rather than badly:
  * the file is re-checked against the gate's limits before it is copied --
    at most 1 MiB, at most 1024x1024, and a real PNG by magic bytes;
  * the copy is atomic, so a partial write can never be graded;
  * every failure exits non-zero with a line saying what was wrong.

The output name is fixed by the competition: entry.png, whatever the format.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile

# the rendered image, committed beside this file
SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "entry.png")

# the competition names the file exactly; keep it even though the format is PNG
OUTPUT_NAME = "entry.png"

DEFAULT_OUT_DIR = "/output"

MAX_BYTES = 1048576          # the gate rejects anything larger
MAX_SIDE = 1024              # and anything wider or taller than this
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def fail(message):
    """Say what went wrong and stop, rather than writing a file that fails the gate."""
    print(f"error: {message}", file=sys.stderr)
    return 1


def png_size(data):
    """Read width and height out of the IHDR chunk, without trusting anything else."""
    if len(data) < 24 or not data.startswith(PNG_MAGIC):
        raise ValueError("not a PNG")
    if data[12:16] != b"IHDR":
        raise ValueError("first chunk is not IHDR")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def check_output_dir(out_dir):
    """The grader hands us a directory that exists; a typo should not make one."""
    if os.path.isdir(out_dir):
        return None
    parent = os.path.dirname(os.path.abspath(out_dir)) or "/"
    if not os.path.isdir(parent):
        return f"{out_dir} has no parent directory"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        return f"cannot create {out_dir}: {exc}"
    return None


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", DEFAULT_OUT_DIR)

    if not os.path.isfile(SOURCE):
        return fail(f"the image is missing: {SOURCE}")

    size = os.path.getsize(SOURCE)
    if size > MAX_BYTES:
        return fail(f"the image is {size} bytes, over the {MAX_BYTES}-byte limit")

    with open(SOURCE, "rb") as fh:
        head = fh.read(24)
    try:
        w, h = png_size(head)
    except ValueError as exc:
        return fail(f"the image is not a usable PNG: {exc}")
    if w > MAX_SIDE or h > MAX_SIDE:
        return fail(f"the image is {w}x{h}, over the {MAX_SIDE}px limit")

    problem = check_output_dir(out_dir)
    if problem:
        return fail(problem)
    dest = os.path.join(out_dir, OUTPUT_NAME)

    # atomic: write beside the target, then rename over it, so the grader never
    # sees a half-written file if the run is cut short
    fd, tmp = tempfile.mkstemp(dir=out_dir, prefix=".entry-", suffix=".png")
    os.close(fd)
    try:
        shutil.copyfile(SOURCE, tmp)
        os.replace(tmp, dest)
    except OSError as exc:
        if os.path.exists(tmp):
            os.unlink(tmp)
        return fail(f"could not write {dest}: {exc}")

    written = os.path.getsize(dest)
    print(f"wrote {dest} ({written} bytes, {w}x{h})")
    return 0 if written == size else fail(f"{dest} is {written} bytes, expected {size}")


if __name__ == "__main__":
    raise SystemExit(main())
