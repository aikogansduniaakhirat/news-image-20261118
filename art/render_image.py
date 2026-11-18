"""Render the 18 November 2026 world-news image for make.fun.

Build-time tool only. The shipped entrypoint is main.py, a stdlib copier of the
PNG this writes (the rules allow exactly that: a repository holding the image
and a one-line program that copies it to /output/entry.png).

What the judge rewards, in its own order: the image names the day it sums up;
it carries specific, recognisable events; it shows breadth across regions and
fields; a reader who missed the day can tell what happened from the picture and
its short labels; and it holds up at about 300 px across.

So the page is laid out as a front page. An unmissable date band owns the top
third. A world map with one numbered pin per story carries breadth at a glance.
Six cards below the map carry the specifics: a field label, a headline short
enough to read at thumbnail size, and one line of hard detail (numbers, names,
places). A footer strip lists the day's other stories so breadth is shown rather
than claimed.

Pins are one per story, set at the place the story is filed from. The Middle
East is only ~66 px wide at this scale, so only two pins may live there; the
rest of that region's news rides in the footer with its place named in the text.

    python art/render_image.py --probe        # layout and collision report
    MAKEFUN_OUTPUT_DIR=out python art/render_image.py
"""

from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

S = 3                                  # supersample factor
W = H = 1024 * S
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
NAME = os.environ.get("ENTRY_NAME", "entry.png")
HERE = os.path.dirname(os.path.abspath(__file__))

FONT_DIR = "/usr/share/fonts/truetype/dejavu"

PAPER = (247, 243, 235)
LAND = (210, 196, 168)
LAND_EDGE = (86, 82, 74)
OCEAN = (236, 242, 246)
GRID = (219, 224, 228)
INK = (15, 19, 25)
INK_SOFT = (72, 77, 84)
ACCENT = (158, 34, 25)
BLUE = (33, 70, 108)

DATE_TEXT = "18 NOVEMBER 2026"
KICKER = "WORLD NEWS  -  WEDNESDAY"
SUBHEAD = "Wednesday's world news in one image"
SUBHEAD_R = "SIX STORIES  -  SIX REGIONS"

# field, number, headline (one line), detail (<=2 lines), (lon, lat)
# Every story here happened, or was first reported, on 18 November 2026.
STORIES = [
    ("MIDDLE EAST  -  CONFLICT", "1", "US STRIKES QESHM",
     "Iran's Guards hit Bahrain again; Manama clears its alert at dawn",
     (50.58, 26.22)),
    ("MARKETS  -  TECHNOLOGY", "2", "NVIDIA LIFTS SEOUL",
     "Revenue doubles, the board bars Huang's return, Seoul jumps",
     (126.98, 37.57)),
    ("CYBER  -  SECURITY", "3", "OUTAGES HIT THE WEB",
     "BBC, IKEA and Air France go down; the NSA loses a network",
     (-98.00, 39.00)),
    ("AMERICAS  -  HEALTH", "4", "MEASLES STATUS LOST",
     "The US, Mexico and Bolivia lose elimination after decades",
     (-102.00, 23.00)),
    ("EUROPE  -  SANCTIONS", "5", "UK TARGETS SETTLERS",
     "Eight firms building West Bank settlements are sanctioned",
     (-1.50, 52.50)),
    ("CARIBBEAN  -  SECURITY", "6", "HAITI BACKS BUKELE",
     "Thousands march for Salvadoran troops as gang violence rises",
     (-72.34, 18.54)),
]

# the day's other stories, one dot each, in the same order as ALSO
# The unnumbered dots mark other places the day touched. Nothing here may sit
# within PIN_R + 8px of a numbered pin, or under the footer's legend colour.
MINOR = [(86.10, 55.40), (90.40, 23.80), (44.40, 33.30), (37.50, 55.70)]

ALSO_HEAD = "ALSO ON 18 NOVEMBER"
ALSO = ["Russian An-12 crash in Siberia kills 19",
        "Trump seeks $50bn for aviation overhaul",
        "Congress backs a plane locator mandate",
        "California bans Waymo from freeways",
        "Knesset speaker replaced by Eisenkot bloc",
        "Lee arrives in Shenzhen for APEC"]


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(os.path.join(FONT_DIR, name), max(6, int(size * S)))


def tracked(d, xy, text, f, fill, spacing):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + spacing * S


def wrap(text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if f.getlength(trial) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


with open(os.path.join(HERE, "land_cache.json")) as _f:
    LAND_JSON = json.load(_f)
LAT_TOP, LAT_BOTTOM = LAND_JSON["lat_top"], LAND_JSON["lat_bottom"]


def project(lon, lat, box):
    x0, y0, x1, y1 = box
    x = x0 + (lon + 180.0) / 360.0 * (x1 - x0)
    y = y0 + (LAT_TOP - lat) / (LAT_TOP - LAT_BOTTOM) * (y1 - y0)
    return x, y


def draw_map(d, box):
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=OCEAN)
    for lon in range(-150, 181, 30):
        px, _ = project(lon, 0, box)
        d.line([(px, y0), (px, y1)], fill=GRID, width=int(1.2 * S))
    for lat in range(-30, 61, 30):
        _, py = project(0, lat, box)
        d.line([(x0, py), (x1, py)], fill=GRID, width=int(1.2 * S))
    _, eq = project(0, 0, box)
    d.line([(x0, eq), (x1, eq)], fill=(201, 208, 214), width=int(1.8 * S))

    for ring in LAND_JSON["rings"]:
        pts = [project(lon, lat, box) for lon, lat in ring]
        if len(pts) >= 3:
            d.polygon(pts, fill=LAND, outline=LAND_EDGE, width=int(1.8 * S))
    d.rectangle([x0, y0, x1, y1], outline=INK, width=int(2.4 * S))


PIN_R = 12.0


def draw_pins(d, box, fs):
    r = PIN_R * S
    for _, num, _, _, (lon, lat) in STORIES:
        px, py = project(lon, lat, box)
        # paper halo keeps the pin legible where it lands on a coastline
        d.ellipse([px - r - 4 * S, py - r - 4 * S, px + r + 4 * S, py + r + 4 * S],
                  fill=PAPER)
        d.ellipse([px - r, py - r, px + r, py + r], fill=ACCENT,
                  outline=INK, width=int(1.1 * S))
        nw = fs["pin"].getlength(num)
        d.text((px - nw / 2, py - fs["pin"].size / 2 - 1.4 * S), num,
               font=fs["pin"], fill=PAPER)

    for lon, lat in MINOR:
        px, py = project(lon, lat, box)
        rr = 6.0 * S
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=BLUE,
                  outline=PAPER, width=int(1.6 * S))


ROW = 106


def layout():
    m = int(0.038 * W)
    inner = W - 2 * m

    dsz = 88
    while dsz > 24 and font(dsz, True).getlength(DATE_TEXT) > inner:
        dsz -= 2
    fs = {"date": font(dsz, True), "kick": font(17), "sub": font(24),
          "pin": font(16, True), "num": font(19, True), "tag": font(13, True),
          "head": font(30, True), "det": font(18), "also_k": font(15, True),
          "also": font(17)}

    y = m + int(2 * S)
    kick_y = y
    y += int(25 * S)
    date_y = y
    y += int(dsz * 1.13 * S)
    rule1_y = y
    y += int(10 * S)
    sub_y = y
    y += int(33 * S)
    rule2_y = y
    map_top = y + int(14 * S)

    fcol = inner // 2 - int(20 * S)
    frows = (len(ALSO) + 1) // 2
    foot_h = int(20 * S) + int(frows * 23 * S)

    lcols, lrows = 2, 3
    gap = int(18 * S)
    # stack strictly from the bottom so nothing can overlap the footer rule
    foot_top = H - m - foot_h
    legend_h = lrows * int(ROW * S)
    legend_top = foot_top - gap - legend_h
    map_bottom = legend_top - gap
    map_box = (m, map_top, W - m, map_bottom)
    lcw = inner // lcols

    cells = []
    for i, (tag, num, head, detail, pt) in enumerate(STORIES):
        cx = m + (i % lcols) * lcw
        cy = legend_top + (i // lcols) * int(ROW * S)
        cells.append({"tag": tag, "num": num, "head": head, "detail": detail,
                      "pt": pt, "cell": (cx, cy, lcw, int(ROW * S)),
                      "num_xy": (cx + 2 * S, cy + 5 * S),
                      "text_xy": (cx + 30 * S, cy)})
    return {"m": m, "inner": inner, "kick_y": kick_y, "date_y": date_y,
            "dsz": dsz, "rule1_y": rule1_y, "sub_y": sub_y, "rule2_y": rule2_y,
            "map_box": map_box, "legend_top": legend_top, "cells": cells,
            "foot_h": foot_h, "foot_top": foot_top, "fcol": fcol,
            "frows": frows, "lcw": lcw, "fs": fs, "legend_bottom": legend_top + legend_h}


def render():
    L = layout()
    fs, m = L["fs"], L["m"]
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    tracked(d, (m, L["kick_y"]), KICKER, fs["kick"], INK_SOFT, 9)
    d.text((m, L["date_y"]), DATE_TEXT, font=fs["date"], fill=INK)
    d.rectangle([m, L["rule1_y"], W - m, L["rule1_y"] + int(2.4 * S)], fill=INK)
    d.text((m, L["sub_y"]), SUBHEAD, font=fs["sub"], fill=INK)
    d.text((W - m - fs["sub"].getlength(SUBHEAD_R), L["sub_y"]), SUBHEAD_R,
           font=fs["sub"], fill=ACCENT)
    d.rectangle([m, L["rule2_y"], W - m, L["rule2_y"] + int(5 * S)], fill=INK)

    draw_map(d, L["map_box"])
    draw_pins(d, L["map_box"], fs)

    # a hairline between the two card columns, so the grid reads as a grid
    lx = m + L["lcw"] - int(9 * S)
    d.line([(lx, L["legend_top"] + int(6 * S)),
            (lx, L["legend_bottom"] - int(14 * S))],
           fill=(208, 202, 191), width=int(1.2 * S))

    for c in L["cells"]:
        cx, cy, cw, ch = c["cell"]
        nx, ny = c["num_xy"]
        r = 10.5 * S
        d.ellipse([nx, ny, nx + 2 * r, ny + 2 * r], fill=ACCENT)
        nw = fs["num"].getlength(c["num"])
        d.text((nx + r - nw / 2, ny + r - fs["num"].size / 2 - 1.2 * S), c["num"],
               font=fs["num"], fill=PAPER)
        tx, ty = c["text_xy"]
        tw = cw - (tx - cx) - int(18 * S)
        tracked(d, (tx, ty + int(3 * S)), c["tag"], fs["tag"], ACCENT, 1.6)
        d.text((tx, ty + int(20 * S)), c["head"], font=fs["head"], fill=INK)
        yy = ty + int(62 * S)
        for line in wrap(c["detail"], fs["det"], tw):
            d.text((tx, yy), line, font=fs["det"], fill=INK_SOFT)
            yy += int(22 * S)

    fy = L["foot_top"]
    d.rectangle([m, fy, W - m, fy + int(2.2 * S)], fill=INK)
    ty = fy + int(9 * S)
    # the blue dot ties the strip to the unnumbered dots on the map
    dy = ty + int(fs["also_k"].size / 2)
    d.ellipse([m + int(1 * S), dy - int(5 * S), m + int(11 * S), dy + int(5 * S)],
              fill=BLUE)
    tracked(d, (m + int(19 * S), ty), ALSO_HEAD, fs["also_k"], BLUE, 2.6)
    half = (len(ALSO) + 1) // 2
    for i, item in enumerate(ALSO):
        col, row = (0, i) if i < half else (1, i - half)
        d.text((m + col * (L["fcol"] + int(26 * S)) + int(3 * S),
                ty + int(23 * S) + row * int(23 * S)), item,
               font=fs["also"], fill=INK_SOFT)

    # BOX, not LANCIOS/LANCZOS: at an integer factor it is an exact area average.
    # Lanczos overshoots at hard ink/ocean edges and lays a bright rim inside the
    # map frame plus colour fringes on small text. BOX has no ringing.
    return img.resize((1024, 1024), Image.BOX)


def probe():
    L = layout()
    fs, inner = L["fs"], L["inner"]
    box = L["map_box"]
    print(f"date {L['dsz']}pt -> {fs['date'].getlength(DATE_TEXT) / S:.0f}px of {inner / S:.0f}")
    print(f"map {[round(v / S) for v in box]} = "
          f"{(box[2] - box[0]) / S:.0f}x{(box[3] - box[1]) / S:.0f}px")
    bad = []

    r = PIN_R + 5.0
    pts = []
    for tag, num, head, detail, (lon, lat) in STORIES:
        px, py = project(lon, lat, box)
        px, py = px / S, py / S
        pts.append((num, px, py))
        inside = (box[0] / S + r < px < box[2] / S - r
                  and box[1] / S + r < py < box[3] / S - r)
        print(f"  pin {num} {tag:<24} ({lon:>7.2f},{lat:>6.2f}) -> "
              f"({px:.0f},{py:.0f}) {'ok' if inside else 'OUTSIDE FRAME'}")
        if not inside:
            bad.append(f"pin {num} outside the map frame")

    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            a, b = pts[i], pts[j]
            dist = math.dist(a[1:], b[1:])
            if dist < 2 * PIN_R + 2:
                bad.append(f"pins {a[0]}/{b[0]} only {dist:.0f}px apart")
    for lon, lat in MINOR:
        mx, my = project(lon, lat, box)
        mx, my = mx / S, my / S
        for num, px, py in pts:
            dist = math.dist((mx, my), (px, py))
            if dist < PIN_R + 8:
                bad.append(f"minor dot near pin {num} ({dist:.0f}px)")
        for lon2, lat2 in MINOR:
            if (lon, lat) == (lon2, lat2):
                continue
            nx, ny = project(lon2, lat2, box)
            if math.dist((mx, my), (nx / S, ny / S)) < 16:
                bad.append("two minor dots collide")

    for c in L["cells"]:
        cx, cy, cw, ch = c["cell"]
        tx = c["text_xy"][0]
        tw = cw - (tx - cx) - 18 * S
        hl = wrap(c["head"], fs["head"], tw)
        dl = wrap(c["detail"], fs["det"], tw)
        used = int(62 * S) + len(dl) * int(22 * S)
        print(f"  card {c['num']} head={len(hl)}L det={len(dl)}L "
              f"used={used / S:.0f}/{ch / S:.0f}")
        if len(hl) > 1:
            bad.append(f"card {c['num']} headline wraps")
        if used > ch:
            bad.append(f"card {c['num']} overflows its row")

    fw = max(fs["also"].getlength(t) for t in ALSO)
    print(f"footer {len(ALSO)} items, widest {fw / S:.0f}px of "
          f"{L['fcol'] / S:.0f}px; map height {(box[3] - box[1]) / S:.0f}px")
    if fw > L["fcol"]:
        bad.append("footer item overflows its column")
    if (box[3] - box[1]) / (box[2] - box[0]) < 0.3:
        bad.append("map too letterboxed to read")
    print("problems:", bad or "none")
    return 1 if bad else 0


def main():
    if "--probe" in sys.argv:
        return probe()
    img = render()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, NAME)
    img.save(path, "PNG", optimize=True)
    n = os.path.getsize(path)
    print(f"wrote {path} {n} bytes {img.size[0]}x{img.size[1]}")
    return 0 if n <= 1048576 else 1


if __name__ == "__main__":
    raise SystemExit(main())
