#!/usr/bin/env python3
"""make.fun entry: one image summing up Wednesday 18 November 2026.

The competition asks for a single image of the day's world news, produced by a
program that runs offline. The rules name the simplest compliant shape outright:
a repository that holds the image plus a program that copies it into the output
directory. This is that program, and art/entry.png is that image.

    MAKEFUN_OUTPUT_DIR=out python3 main.py

Nothing is drawn here. art/render_image.py draws the page once, at build time,
with Pillow; the result is committed. Copying a committed file is byte-identical
across runs by definition, which is exactly what the two-run reproducibility
check wants and is why the split exists at all.

A malformed image is not scored badly, it is scored zero, so the checks below run
before anything is written:

  * the source is a real PNG (magic bytes) with a plausible IHDR;
  * it is within the gate's limits, 1 MiB and 1024 px a side;
  * the copy is atomic, so a truncated file can never be graded;
  * the byte count of what landed is compared with the source.

The output filename is fixed by the competition, not by this program.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGE = os.path.join(HERE, "art", "entry.png")

OUTPUT_NAME = "entry.png"
DEFAULT_OUT = "/output"

LIMIT_BYTES = 1024 * 1024
LIMIT_SIDE = 1024
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def abort(reason):
    """Report and stop: a wrong file in the output dir is worse than no file."""
    sys.stderr.write("error: %s\n" % reason)
    return 1


def dimensions(head):
    """Width and height from the IHDR chunk, with the structure actually checked."""
    if not head.startswith(PNG_SIG):
        raise ValueError("signature is not PNG")
    if len(head) < 24:
        raise ValueError("header is truncated")
    if head[12:16] != b"IHDR":
        raise ValueError("first chunk is not IHDR")
    width = int.from_bytes(head[16:20], "big")
    height = int.from_bytes(head[20:24], "big")
    if width == 0 or height == 0:
        raise ValueError("header declares a zero side")
    return width, height


def resolve_out_dir():
    """Honour the grader's directory; never silently invent a different one."""
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", DEFAULT_OUT)
    if os.path.isdir(out_dir):
        return out_dir, None
    parent = os.path.dirname(os.path.abspath(out_dir)) or "/"
    if not os.path.isdir(parent):
        return None, "%s and its parent both missing" % out_dir
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        return None, "cannot create %s (%s)" % (out_dir, exc)
    return out_dir, None


def main():
    if not os.path.isfile(IMAGE):
        return abort("image not found at %s" % IMAGE)

    size = os.path.getsize(IMAGE)
    if size > LIMIT_BYTES:
        return abort("image is %d bytes, limit is %d" % (size, LIMIT_BYTES))

    with open(IMAGE, "rb") as fh:
        head = fh.read(24)
    try:
        width, height = dimensions(head)
    except ValueError as exc:
        return abort("image is unusable: %s" % exc)
    if max(width, height) > LIMIT_SIDE:
        return abort("image is %dx%d, limit is %d a side"
                     % (width, height, LIMIT_SIDE))

    out_dir, problem = resolve_out_dir()
    if problem:
        return abort(problem)

    target = os.path.join(out_dir, OUTPUT_NAME)
    # write beside the target and rename over it: the grader either sees the
    # whole file or no file, never a half-copied one
    handle, scratch = tempfile.mkstemp(dir=out_dir, prefix=".entry-", suffix=".png")
    os.close(handle)
    try:
        shutil.copyfile(IMAGE, scratch)
        os.replace(scratch, target)
    except OSError as exc:
        if os.path.exists(scratch):
            os.unlink(scratch)
        return abort("could not write %s (%s)" % (target, exc))

    written = os.path.getsize(target)
    if written != size:
        return abort("%s holds %d bytes, expected %d" % (target, written, size))

    # the second half of the reproducibility check: the file that landed must
    # still declare the same geometry the source did
    with open(target, "rb") as fh:
        landed = fh.read(24)
    try:
        w2, h2 = dimensions(landed)
    except ValueError as exc:
        return abort("the copy came out unreadable: %s" % exc)
    if (w2, h2) != (width, height):
        return abort("the copy is %dx%d, the source was %dx%d"
                     % (w2, h2, width, height))

    print("wrote %s: %d bytes, %dx%d" % (target, written, width, height))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
