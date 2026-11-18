"""Compose the 18 November 2026 front page that this entry ships.

Build-time only. The entry is ``main.py`` at the repository root; it copies the
finished PNG and never imports Pillow. Keeping the drawing on this side of the
line is what lets the graded program stay standard-library and byte-stable.

The page is four bands stacked in a single column:

    kicker + date     the day, set as wide as the sheet allows
    standfirst        one clause about what the six stories have in common
    map               equirectangular world, six numbered pins
    cards             two columns of three: field, headline, hard detail
    footer            six further items, so breadth is visible

All facts are literals dated 18 November 2026 by at least one wire feed, which
is the brief's test ("happened, or was first reported, on that day in any time
zone"). Nothing here touches the network.

    python art/render_image.py --probe        geometry report; non-zero on trouble
    MAKEFUN_OUTPUT_DIR=art python art/render_image.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# canvas
# ---------------------------------------------------------------------------

SS = 3                       # every coordinate below is in 3x space
SHEET = 1024 * SS
SIDE = 1024                  # what the grader receives
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
OUT_NAME = os.environ.get("ENTRY_NAME", "entry.png")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"

# ---------------------------------------------------------------------------
# palette — also imported by check_image.py, so it cannot drift
# ---------------------------------------------------------------------------

NEWS = (250, 246, 239)       # uncoated paper
SEA = (233, 240, 245)        # water
GEO = (209, 194, 165)        # land
COAST = (78, 74, 66)         # coastline
GUIDE = (219, 223, 227)      # graticule
BLACK = (17, 20, 26)         # body ink
GREY = (78, 83, 90)          # secondary ink
RED = (156, 34, 26)          # pins and field labels
NAVY = (32, 68, 106)         # unnumbered dots

DAY = "18 NOVEMBER 2026"
KICKER = "WORLD NEWS  \u00b7  WEDNESDAY"
STANDFIRST = "The day in six stories"
STAT = "SIX REGIONS  \u00b7  FOUR CONTINENTS"

PIN_R = 11.5
DOT_R = 5.5
CARD_H = 108
GUTTER = 17


class Story(NamedTuple):
    """One card: what it is filed under, its number, and where it happened."""

    field: str
    number: str
    headline: str
    detail: str
    lon: float
    lat: float


# The six, chosen across the map rather than across one wire's front page.
STORIES = [
    Story("MIDDLE EAST \u00b7 CONFLICT", "1", "US STRIKES QESHM",
          "Iran's Guards hit Bahrain again; Kuwait and Manama repel drones.",
          50.58, 26.22),
    Story("ASIA \u00b7 MARKETS", "2", "NVIDIA LIFTS SEOUL",
          "Sales double, the board rules out Huang's return, the Kospi adds 2%.",
          126.98, 37.57),
    Story("CYBER \u00b7 SECURITY", "3", "THE WEB GOES DARK",
          "BBC, IKEA and Air France fall over; the NSA loses a classified net.",
          -77.03, 38.90),
    Story("AMERICAS \u00b7 HEALTH", "4", "MEASLES STATUS LOST",
          "The US, Mexico and Bolivia lose elimination after three decades.",
          -102.55, 23.63),
    Story("EUROPE \u00b7 SANCTIONS", "5", "BRITAIN HITS SETTLERS",
          "Eight firms building West Bank settlements are frozen out.",
          -0.13, 51.50),
    Story("CARIBBEAN \u00b7 SECURITY", "6", "HAITI BACKS BUKELE",
          "Thousands march for El Salvador's anti-gang force as fears grow.",
          -72.34, 18.54),
]

# places the day touched that did not earn a card
SPOTS = [(37.62, 55.75), (86.09, 55.35), (0.19, 5.60), (-62.00, -5.00)]

FOOT_LABEL = "ALSO ON THE DAY"
FOOTER = [
    "Russian An-12 crash in Siberia kills 19",
    "Ghana's $60m presidential jet draws anger",
    "Trump seeks $50bn for an aviation overhaul",
    "Brazil tribe emerges from isolation",
    "California bars Waymo from its freeways",
    "Lee reaches Shenzhen for the Apec summit",
]


# ---------------------------------------------------------------------------
# type
# ---------------------------------------------------------------------------

def face(size, *, serif=False, bold=False):
    """One font at one size, pre-scaled into 3x space."""
    stem = "DejaVuSerif" if serif else "DejaVuSans"
    if bold:
        stem += "-Bold"
    return ImageFont.truetype(os.path.join(FONT_DIR, stem + ".ttf"),
                              max(5, int(round(size * SS))))


def tracking(draw, xy, text, font, colour, gap):
    """Letter-spaced text — how a 12pt caps label survives a 300px thumbnail."""
    x, y = xy
    step = gap * SS
    for char in text:
        draw.text((x, y), char, font=font, fill=colour)
        x += font.getlength(char) + step


def tracking_width(text, font, gap):
    return sum(font.getlength(c) for c in text) + gap * SS * max(0, len(text) - 1)


def wrap(text, font, width):
    """Greedy wrap. The caller measures the result; this does not promise fit."""
    rows, row = [], ""
    for word in text.split():
        trial = (row + " " + word).strip()
        if row and font.getlength(trial) > width:
            rows.append(row)
            row = word
        else:
            row = trial
    if row:
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# projection
# ---------------------------------------------------------------------------

with open(os.path.join(HERE, "land_cache.json")) as _fh:
    _WORLD = json.load(_fh)

LAT_TOP = _WORLD["lat_top"]
LAT_BOTTOM = _WORLD["lat_bottom"]
RINGS = _WORLD["rings"]


def place(lon, lat, frame):
    """Equirectangular, in 3x units, inside the given frame."""
    left, top, right, bottom = frame
    x = left + (lon + 180.0) / 360.0 * (right - left)
    y = top + (LAT_TOP - lat) / (LAT_TOP - LAT_BOTTOM) * (bottom - top)
    return x, y


# ---------------------------------------------------------------------------
# layout — derived bottom-up so no band can collide with the one below it
# ---------------------------------------------------------------------------

def layout():
    margin = int(0.036 * SHEET)
    span = SHEET - 2 * margin

    date_pt = 86
    while date_pt > 30 and face(date_pt, serif=True, bold=True).getlength(DAY) > span:
        date_pt -= 1

    fonts = {
        "kick": face(16), "date": face(date_pt, serif=True, bold=True),
        "stand": face(25, serif=True), "stat": face(14),
        "tag": face(12, bold=True), "head": face(28, serif=True, bold=True),
        "detail": face(17), "pin": face(15, bold=True),
        "badge": face(18, bold=True), "foot_tag": face(13, bold=True),
        "foot": face(16),
    }

    cursor = margin + 2 * SS
    kick_y = cursor
    cursor += 24 * SS
    date_y = cursor
    cursor += int(date_pt * 1.12 * SS)
    hair_y = cursor
    cursor += 11 * SS
    stand_y = cursor
    cursor += 31 * SS
    bar_y = cursor
    map_top = cursor + 15 * SS

    foot_rows = (len(FOOTER) + 1) // 2
    foot_h = 21 * SS + foot_rows * 22 * SS
    foot_top = SHEET - margin - foot_h

    cards_h = 3 * CARD_H * SS
    cards_top = foot_top - GUTTER * SS - cards_h
    map_bottom = cards_top - GUTTER * SS
    frame = (margin, map_top, SHEET - margin, map_bottom)

    col_w = span // 2
    inset = 27 * SS
    boxes = []
    for i, story in enumerate(STORIES):
        x = margin + (i % 2) * col_w
        y = cards_top + (i // 2) * CARD_H * SS
        boxes.append({
            "story": story,
            "box": (x, y, col_w, CARD_H * SS),
            "badge": (x + 1 * SS, y + 6 * SS),
            "text_x": x + inset,
            "text_w": col_w - inset - 16 * SS,
        })

    return {
        "margin": margin, "span": span, "fonts": fonts, "date_pt": date_pt,
        "kick_y": kick_y, "date_y": date_y, "hair_y": hair_y,
        "stand_y": stand_y, "bar_y": bar_y, "frame": frame,
        "boxes": boxes, "cards_top": cards_top, "cards_h": cards_h,
        "foot_top": foot_top, "foot_h": foot_h, "foot_rows": foot_rows,
        "col_w": col_w, "foot_col": span // 2,
    }


# ---------------------------------------------------------------------------
# painters
# ---------------------------------------------------------------------------

def paint_masthead(draw, plan):
    f, m = plan["fonts"], plan["margin"]
    tracking(draw, (m, plan["kick_y"]), KICKER, f["kick"], GREY, 8.5)
    draw.text((m, plan["date_y"]), DAY, font=f["date"], fill=BLACK)
    draw.line([(m, plan["hair_y"]), (SHEET - m, plan["hair_y"])],
              fill=BLACK, width=int(2.3 * SS))
    draw.text((m, plan["stand_y"]), STANDFIRST, font=f["stand"], fill=BLACK)
    w = tracking_width(STAT, f["stat"], 2.6)
    tracking(draw, (SHEET - m - w, plan["stand_y"] + 8 * SS), STAT,
             f["stat"], RED, 2.6)
    draw.rectangle([m, plan["bar_y"], SHEET - m, plan["bar_y"] + 5 * SS],
                   fill=BLACK)


def paint_map(draw, frame):
    left, top, right, bottom = frame
    draw.rectangle([left, top, right, bottom], fill=SEA)

    for lon in range(-150, 181, 30):
        x, _ = place(lon, 0.0, frame)
        draw.line([(x, top), (x, bottom)], fill=GUIDE, width=int(1.1 * SS))
    for lat in range(-30, 61, 30):
        _, y = place(0.0, lat, frame)
        draw.line([(left, y), (right, y)], fill=GUIDE, width=int(1.1 * SS))

    _, equator = place(0.0, 0.0, frame)
    draw.line([(left, equator), (right, equator)], fill=(198, 206, 212),
              width=int(1.7 * SS))

    for ring in RINGS:
        outline = [place(lon, lat, frame) for lon, lat in ring]
        if len(outline) >= 3:
            draw.polygon(outline, fill=GEO, outline=COAST,
                         width=int(1.7 * SS))

    draw.rectangle([left, top, right, bottom], outline=BLACK,
                   width=int(2.3 * SS))


def paint_markers(draw, frame, pin_font):
    r = PIN_R * SS
    halo = 4 * SS
    for story in STORIES:
        cx, cy = place(story.lon, story.lat, frame)
        draw.ellipse([cx - r - halo, cy - r - halo, cx + r + halo, cy + r + halo],
                     fill=NEWS)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED,
                     outline=BLACK, width=int(1.0 * SS))
        half = pin_font.getlength(story.number) / 2
        draw.text((cx - half, cy - pin_font.size / 2 - 1.2 * SS), story.number,
                  font=pin_font, fill=NEWS)

    for lon, lat in SPOTS:
        cx, cy = place(lon, lat, frame)
        d = DOT_R * SS
        draw.ellipse([cx - d, cy - d, cx + d, cy + d], fill=NAVY,
                     outline=NEWS, width=int(1.5 * SS))


def paint_cards(draw, plan):
    f, m = plan["fonts"], plan["margin"]
    seam = m + plan["col_w"] - int(9 * SS)
    draw.line([(seam, plan["cards_top"] + 4 * SS),
               (seam, plan["cards_top"] + plan["cards_h"] - 12 * SS)],
              fill=(206, 200, 189), width=int(1.1 * SS))

    for slot in plan["boxes"]:
        story = slot["story"]
        x, y, _w, _h = slot["box"]
        bx, by = slot["badge"]

        draw.line([(x, y), (x + 22 * SS, y)], fill=RED, width=int(2.2 * SS))
        radius = 10 * SS
        draw.ellipse([bx, by, bx + 2 * radius, by + 2 * radius], fill=RED)
        num_w = f["badge"].getlength(story.number)
        draw.text((bx + radius - num_w / 2,
                   by + radius - f["badge"].size / 2 - 1.0 * SS),
                  story.number, font=f["badge"], fill=NEWS)

        tx = slot["text_x"]
        tracking(draw, (tx, y + 3 * SS), story.field, f["tag"], RED, 1.5)
        draw.text((tx, y + 19 * SS), story.headline, font=f["head"], fill=BLACK)

        cursor = y + 60 * SS
        for row in wrap(story.detail, f["detail"], slot["text_w"]):
            draw.text((tx, cursor), row, font=f["detail"], fill=GREY)
            cursor += 21 * SS


def paint_footer(draw, plan):
    f, m, top = plan["fonts"], plan["margin"], plan["foot_top"]
    draw.rectangle([m, top, SHEET - m, top + 2.2 * SS], fill=BLACK)

    label_y = top + 9 * SS
    dot_y = label_y + f["foot_tag"].size / 2
    draw.ellipse([m, dot_y - 4.5 * SS, m + 9 * SS, dot_y + 4.5 * SS], fill=NAVY)
    tracking(draw, (m + 17 * SS, label_y), FOOT_LABEL, f["foot_tag"], NAVY, 2.4)

    split = (len(FOOTER) + 1) // 2
    for i, item in enumerate(FOOTER):
        col, row = (0, i) if i < split else (1, i - split)
        x = m + col * (plan["foot_col"] + 24 * SS) + 2 * SS
        y = label_y + 22 * SS + row * 22 * SS
        draw.text((x, y), item, font=f["foot"], fill=GREY)


def render():
    plan = layout()
    sheet = Image.new("RGB", (SHEET, SHEET), NEWS)
    draw = ImageDraw.Draw(sheet)

    paint_masthead(draw, plan)
    paint_map(draw, plan["frame"])
    paint_markers(draw, plan["frame"], plan["fonts"]["pin"])
    paint_cards(draw, plan)
    paint_footer(draw, plan)

    # BOX, not LANCZOS: at an exact 3x factor it averages each block, so ink
    # edges get no overshoot ring and 12pt caps keep their weight.
    return sheet.resize((SIDE, SIDE), Image.BOX)


# ---------------------------------------------------------------------------
# geometry self-check
# ---------------------------------------------------------------------------

def probe():
    plan = layout()
    f = plan["fonts"]
    frame = plan["frame"]
    faults = []

    print("date %dpt -> %.0f of %.0f px"
          % (plan["date_pt"], f["date"].getlength(DAY) / SS, plan["span"] / SS))
    print("map %.0fx%.0f px at y=%.0f" % ((frame[2] - frame[0]) / SS,
                                         (frame[3] - frame[1]) / SS,
                                         frame[1] / SS))

    pins = []
    for story in STORIES:
        x, y = place(story.lon, story.lat, frame)
        px, py = x / SS, y / SS
        pins.append((story.number, px, py))
        clear = PIN_R + 4
        inside = (frame[0] / SS + clear < px < frame[2] / SS - clear
                  and frame[1] / SS + clear < py < frame[3] / SS - clear)
        print("  pin %s at (%4.0f,%4.0f) %s"
              % (story.number, px, py, "in frame" if inside else "OUT OF FRAME"))
        if not inside:
            faults.append("pin %s leaves the map frame" % story.number)

    for i in range(len(pins)):
        for j in range(i + 1, len(pins)):
            gap = math.dist(pins[i][1:], pins[j][1:])
            if gap < 2 * PIN_R + 2:
                faults.append("pins %s/%s only %.0f px apart"
                              % (pins[i][0], pins[j][0], gap))

    for lon, lat in SPOTS:
        sx, sy = place(lon, lat, frame)
        for number, px, py in pins:
            if math.dist((sx / SS, sy / SS), (px, py)) < PIN_R + 8:
                faults.append("dot collides with pin %s" % number)

    for slot in plan["boxes"]:
        story = slot["story"]
        head_w = f["head"].getlength(story.headline)
        rows = wrap(story.detail, f["detail"], slot["text_w"])
        tag_w = tracking_width(story.field, f["tag"], 1.5)
        used = 60 * SS + len(rows) * 21 * SS
        print("  card %s: head %.0f/%.0f px, detail %d line(s), used %d/%d"
              % (story.number, head_w / SS, slot["text_w"] / SS, len(rows),
                 used / SS, CARD_H))
        if head_w > slot["text_w"]:
            faults.append("card %s headline overruns its column" % story.number)
        if tag_w > slot["text_w"]:
            faults.append("card %s label overruns its column" % story.number)
        if used > CARD_H * SS:
            faults.append("card %s overflows its row" % story.number)

    widest = max(f["foot"].getlength(t) for t in FOOTER)
    print("footer widest %.0f of %.0f px; map height %.0f px; footer top %.0f"
          % (widest / SS, plan["foot_col"] / SS, (frame[3] - frame[1]) / SS,
             plan["foot_top"] / SS))
    if widest > plan["foot_col"]:
        faults.append("a footer item overruns its column")
    if (frame[3] - frame[1]) / (frame[2] - frame[0]) < 0.3:
        faults.append("map is too letterboxed to read")

    print("faults:", faults or "none")
    return 1 if faults else 0


def main():
    if "--probe" in sys.argv:
        return probe()

    image = render()
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, OUT_NAME)
    image.save(path, "PNG", optimize=True)

    size = os.path.getsize(path)
    print("wrote %s: %d bytes, %dx%d" % (path, size, image.size[0], image.size[1]))
    if size > 1048576:
        print("error: over the 1 MiB cap", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
