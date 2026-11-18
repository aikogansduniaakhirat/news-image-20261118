"""Measure a candidate front-page PNG against what the brief actually asks for.

No vision model is reachable while this entry is built, so the image is judged
here by counting pixels rather than by looking at it. Each question has a
defensible answer:

  1. is the date really the heaviest thing on the sheet?
  2. does the map frame hold land, and is land where geography puts it?
  3. is there a red pin at every story's projected centre?
  4. does the page survive the 300 px downscale the judge reads it at?

Thresholds are compared in the same unit the helper returns — a fraction against
a fraction. Mixing a fraction with a percentage is how a checker starts reporting
that a dense masthead is empty.

    python art/check_image.py art/entry.png
"""

from __future__ import annotations

import os
import sys

from PIL import Image

# Take the palette and the projection from the renderer rather than retyping
# them: a checker holding its own copy of the colours goes stale the moment the
# palette moves, and then argues with an image it drew itself.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_image as R  # noqa: E402

JUDGE_SIDE = 300        # the size the picture is read at
INK = 118               # mean channel below this counts as ink
HOOD = 2                # +/- pixels sampled per geography probe


def mean(pixel):
    return (pixel[0] + pixel[1] + pixel[2]) / 3.0


def near(pixel, colour, slack=26):
    return all(abs(pixel[i] - colour[i]) <= slack for i in range(3))


def ink_share(image, box):
    """Fraction of dark pixels in a box, in 0..1."""
    crop = image.crop(box).convert("RGB")
    pixels = list(crop.getdata())
    return sum(1 for p in pixels if mean(p) < INK) / max(1, len(pixels))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "art/entry.png"
    image = Image.open(path).convert("RGB")
    width, height = image.size
    size = os.path.getsize(path)
    faults = []

    print("file %s: %dx%d, %d bytes" % (path, width, height, size))
    if (width, height) != (1024, 1024):
        faults.append("not 1024x1024")
    if size > 1048576:
        faults.append("over 1 MiB")

    # 1. the date has to dominate the top band, or the page could be any day
    top = ink_share(image, (0, 0, width, 300))
    body = ink_share(image, (0, 300, width, 900))
    print("ink: masthead band %.1f%%, body %.1f%%" % (top * 100, body * 100))
    if top < 0.06:
        faults.append("masthead band looks empty (%.1f%% ink)" % (top * 100))
    if top <= body:
        faults.append("date band is not the densest part of the page")

    # 2. the map frame must be drawing, not blank paper
    plan = R.layout()
    fl, ft, fr, fb = [v / R.SS for v in plan["frame"]]
    frame_box = (int(fl), int(ft), int(fr), int(fb))
    crop = image.crop(frame_box).convert("RGB")
    total = crop.size[0] * crop.size[1]
    land = sum(1 for p in crop.getdata() if near(p, R.GEO, 18))
    sea = sum(1 for p in crop.getdata() if near(p, R.SEA, 14))
    print("map: land %.1f%%, sea %.1f%%, other %.1f%%"
          % (100 * land / total, 100 * sea / total,
             100 * (total - land - sea) / total))
    if land / total < 0.18:
        faults.append("map frame carries almost no land")
    if (land + sea) / total < 0.85:
        faults.append("map frame is not filled by the drawing")

    # 3. geography, at coordinates whose answer is not in doubt. Sample a
    #    neighbourhood and take the majority: a graticule hairline or a marker
    #    halo can sit exactly on a single pixel and prove nothing.
    def classify(lon, lat):
        x, y = R.place(lon, lat, (fl, ft, fr, fb))
        x, y = int(x), int(y)
        tally = {"land": 0, "sea": 0, "other": 0}
        for dx in range(-HOOD, HOOD + 1):
            for dy in range(-HOOD, HOOD + 1):
                pixel = image.getpixel((min(width - 1, max(0, x + dx)),
                                        min(height - 1, max(0, y + dy))))
                if near(pixel, R.GEO, 30):
                    tally["land"] += 1
                elif near(pixel, R.SEA, 26):
                    tally["sea"] += 1
                else:
                    tally["other"] += 1
        return max(tally, key=tally.get), tally

    for name, lon, lat, want in [
        ("Sahara", 10.0, 22.0, "land"), ("Siberia", 100.0, 62.0, "land"),
        ("Kansas", -98.0, 38.5, "land"), ("Amazon", -68.0, -8.0, "land"),
        ("Alice Springs", 133.8, -23.7, "land"), ("Congo", 22.0, -2.0, "land"),
        ("Atlantic", -35.0, 10.0, "sea"), ("Pacific", -150.0, -8.0, "sea"),
        ("Indian Ocean", 75.0, -20.0, "sea"),
        ("Bay of Bengal", 88.0, 14.0, "sea"),
    ]:
        got, tally = classify(lon, lat)
        ok = got == want
        print("  %-14s %-5s -> %-5s %-8s %s"
              % (name, want, got, "ok" if ok else "MISMATCH", tally))
        if not ok:
            faults.append("geography mismatch at %s (%s, wanted %s)"
                          % (name, got, want))

    # 4. a red pin within a pin radius of each story's projected centre
    reach = int(R.PIN_R)
    for story in R.STORIES:
        x, y = R.place(story.lon, story.lat, (fl, ft, fr, fb))
        x, y = int(x), int(y)
        found = any(
            near(image.getpixel((min(width - 1, max(0, x + dx)),
                                 min(height - 1, max(0, y + dy)))), R.RED, 40)
            for dx in range(-reach, reach + 1)
            for dy in range(-reach, reach + 1)
        )
        print("  pin %s at (%d,%d): %s"
              % (story.number, x, y, "red found" if found else "MISSING"))
        if not found:
            faults.append("no pin drawn for story %s" % story.number)

    # 5. the judge reads a thumbnail — contrast has to survive the downscale
    thumb = image.resize((JUDGE_SIDE, JUDGE_SIDE), Image.LANCZOS).convert("RGB")
    values = sorted(mean(p) for p in thumb.getdata())
    dark = sum(1 for v in values if v < INK) / len(values)
    lo = values[int(0.02 * len(values))]
    hi = values[int(0.98 * len(values))]
    print("at %d px: ink %.1f%%, 2-98%% range %.0f..%.0f (spread %.0f)"
          % (JUDGE_SIDE, dark * 100, lo, hi, hi - lo))
    if hi - lo < 120:
        faults.append("thumbnail contrast collapses at %d px" % JUDGE_SIDE)
    if not 0.02 < dark < 0.45:
        faults.append("thumbnail reads as %s"
                      % ("blank" if dark <= 0.02 else "mud"))

    print("faults:", faults or "none")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
