"""Measure a candidate front-page PNG against the things the brief cares about.

No vision model is reachable while this entry is built, so the image is checked
by counting pixels instead of by looking at it. Everything here is a question
with a defensible answer:

  * is the date actually the biggest thing on the page (ink in the top band)?
  * does the map frame hold land, and does land sit where geography says it does?
  * is there a red pin at each story's projected centre?
  * does the page still hold together after the 300 px downscale the judge uses?

    python art/check_image.py art/entry.png
"""

from __future__ import annotations

import os
import sys

from PIL import Image

# kept in step with render_image.py by importing it, so a palette change here
# cannot silently disagree with what was drawn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_image as R  # noqa: E402

JUDGE_SIDE = 300          # the size the brief says the picture is read at
DARK = 118                # mean channel below this counts as ink


def mean(pixel):
    return (pixel[0] + pixel[1] + pixel[2]) / 3.0


def near(pixel, colour, slack=26):
    return all(abs(pixel[i] - colour[i]) <= slack for i in range(3))


def ink_share(image, box):
    crop = image.crop(box).convert("RGB")
    pixels = list(crop.getdata())
    dark = sum(1 for p in pixels if mean(p) < DARK)
    return dark / max(1, len(pixels))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "art/entry.png"
    image = Image.open(path).convert("RGB")
    faults = []
    print("file %s: %dx%d, %d bytes"
          % (path, image.size[0], image.size[1], os.path.getsize(path)))

    if image.size != (1024, 1024):
        faults.append("not 1024x1024")
    if os.path.getsize(path) > 1048576:
        faults.append("over 1 MiB")

    # 1. the date must dominate the top band, or the picture could be any day
    top = ink_share(image, (0, 0, 1024, 300))
    body = ink_share(image, (0, 300, 1024, 900))
    print("ink: masthead band %.1f%%, body %.1f%%" % (top * 100, body * 100))
    if top < 0.06:
        faults.append("masthead band looks empty (%.1f%% ink)" % (top * 100))
    if top <= body:
        faults.append("date band is not the densest part of the page")

    # 2. the map frame must be mostly drawn land + sea, not blank paper
    g = R.geometry()
    fl, ft, fr, fb = [v / R.SS for v in g["frame"]]
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

    # 3. geography spot check: coordinates whose answer is not in doubt.
    # Sample the 5x5 neighbourhood rather than one pixel: at 1024 px a graticule
    # hairline or a marker halo can land exactly on a single coordinate, and one
    # pixel proving nothing is how a checker starts reporting false alarms.
    def sample(lon, lat):
        x, y = R.place(lon, lat, (fl, ft, fr, fb))
        x, y = int(x), int(y)
        counts = {"land": 0, "sea": 0, "other": 0}
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                pixel = image.getpixel((min(1023, max(0, x + dx)),
                                        min(1023, max(0, y + dy))))
                if near(pixel, R.GEO, 30):
                    counts["land"] += 1
                elif near(pixel, R.SEA, 26):
                    counts["sea"] += 1
                else:
                    counts["other"] += 1
        return max(counts, key=counts.get), counts

    for name, lon, lat, want in [
        ("Sahara", 10.0, 22.0, "land"), ("Siberia", 100.0, 62.0, "land"),
        ("Kansas", -98.0, 38.5, "land"), ("Amazon", -68.0, -8.0, "land"),
        ("Alice Springs", 133.8, -23.7, "land"), ("Congo", 22.0, -2.0, "land"),
        ("Atlantic", -35.0, 10.0, "sea"), ("Pacific", -150.0, -8.0, "sea"),
        ("Indian Ocean", 75.0, -20.0, "sea"), ("Bay of Bengal", 88.0, 14.0, "sea"),
    ]:
        got, counts = sample(lon, lat)
        ok = got == want
        print("  %-14s %-6s -> %-6s %s  %s"
              % (name, want, got, "ok" if ok else "MISMATCH", counts))
        if not ok:
            faults.append("geography mismatch at %s (%s, wanted %s)" % (name, got, want))

    # 4. a pin within a pin radius of every story's projected centre
    radius = int(R.PIN_R)
    for _field, number, _headline, _detail, (lon, lat) in R.CARDS:
        x, y = R.place(lon, lat, (fl, ft, fr, fb))
        found = False
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if near(image.getpixel((int(x) + dx, int(y) + dy)), R.RED, 40):
                    found = True
                    break
            if found:
                break
        print("  pin %s at (%.0f,%.0f): %s" % (number, x, y, "red found" if found else "MISSING"))
        if not found:
            faults.append("no pin drawn for story %s" % number)

    # 5. the judge reads a thumbnail: contrast has to survive a 300 px downscale
    thumb = image.resize((JUDGE_SIDE, JUDGE_SIDE), Image.LANCZOS)
    values = sorted(mean(p) for p in thumb.convert("RGB").getdata())
    dark_frac = sum(1 for v in values if v < DARK) / len(values)
    lo, hi = values[int(0.02 * len(values))], values[int(0.98 * len(values))]
    print("at %d px: ink %.1f%%, 2-98%% range %.0f..%.0f (spread %.0f)"
          % (JUDGE_SIDE, dark_frac * 100, lo, hi, hi - lo))
    if hi - lo < 120:
        faults.append("thumbnail contrast collapses at %d px" % JUDGE_SIDE)
    if not 0.02 < dark_frac < 0.45:
        faults.append("thumbnail reads as %s" % ("blank" if dark_frac <= 0.02 else "mud"))

    print("faults:", faults or "none")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
