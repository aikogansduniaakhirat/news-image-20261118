"""Draw the 18 November 2026 front page that this entry submits.

This is a build-time tool, not the entry. The entry itself is ``main.py`` at the
repository root: a standard-library copier that hands the finished PNG to the
grader. Rendering lives here so the entrypoint can stay dependency-free.

The picture is a newspaper front page for one day:

    masthead     the date, set as large as the paper allows
    map          an equirectangular world with one numbered pin per story
    cards        six stories: field label, headline, and a line of hard detail
    footer       six more items from the same day, so breadth is shown

Every story below is dated 18 November 2026 by at least one wire feed, which is
what the brief asks for ("happened, or was first reported, on that day in any
time zone"). The renderer never fetches anything; the facts are literals.

Usage:
    python art/render_image.py --probe     # geometry report, non-zero on trouble
    MAKEFUN_OUTPUT_DIR=out python art/render_image.py
"""

from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

SS = 3                                  # supersampling factor: 3072 -> 1024
PAGE = 1024 * SS
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
OUT_NAME = os.environ.get("ENTRY_NAME", "entry.png")

SERIF_DIR = "/usr/share/fonts/truetype/dejavu"
SANS_DIR = "/usr/share/fonts/truetype/dejavu"

NEWS = (250, 246, 239)          # paper
SEA = (233, 240, 245)
GEO = (209, 194, 165)
COAST = (78, 74, 66)
GUIDE = (219, 223, 227)
BLACK = (17, 20, 26)
GREY = (78, 83, 90)
RED = (156, 34, 26)
NAVY = (32, 68, 106)

DAY = "18 NOVEMBER 2026"
KICKER = "WORLD NEWS  \u00b7  WEDNESDAY"
STANDFIRST = "The day in six stories"
STAT = "SIX REGIONS  \u00b7  FOUR CONTINENTS"

# (field, number, headline, detail, (longitude, latitude) of the filing place)
CARDS = [
    ("MIDDLE EAST \u00b7 CONFLICT", "1", "US STRIKES QESHM",
     "Iran's Guards hit Bahrain again; Kuwait and Manama repel drones.",
     (50.58, 26.22)),
    ("ASIA \u00b7 MARKETS", "2", "NVIDIA LIFTS SEOUL",
     "Sales double, the board rules out Huang's return, the Kospi adds 2%.",
     (126.98, 37.57)),
    ("CYBER \u00b7 SECURITY", "3", "THE WEB GOES DARK",
     "BBC, IKEA and Air France fall over; the NSA loses a classified net.",
     (-77.03, 38.90)),
    ("AMERICAS \u00b7 HEALTH", "4", "MEASLES STATUS LOST",
     "The US, Mexico and Bolivia lose elimination after three decades.",
     (-102.55, 23.63)),
    ("EUROPE \u00b7 SANCTIONS", "5", "BRITAIN HITS SETTLERS",
     "Eight firms building West Bank settlements are frozen out.",
     (-0.13, 51.50)),
    ("CARIBBEAN \u00b7 SECURITY", "6", "HAITI BACKS BUKELE",
     "Thousands march for El Salvador's anti-gang force as fears grow.",
     (-72.34, 18.54)),
]

# places the day touched but that have no card: drawn as small navy dots
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


def face(size, *, serif=False, bold=False):
    """One font at one size, already scaled into supersampled space."""
    family = "DejaVuSerif" if serif else "DejaVuSans"
    if bold:
        family += "-Bold"
    path = os.path.join(SERIF_DIR if serif else SANS_DIR, family + ".ttf")
    return ImageFont.truetype(path, max(5, int(round(size * SS))))


def spaced(draw, xy, text, font, colour, gap):
    """Draw letter-spaced text, which is how small caps labels stay readable."""
    x, y = xy
    step = gap * SS
    for glyph in text:
        draw.text((x, y), glyph, font=font, fill=colour)
        x += font.getlength(glyph) + step


def spaced_width(text, font, gap):
    return sum(font.getlength(g) for g in text) + gap * SS * max(0, len(text) - 1)


def split_lines(text, font, width):
    """Greedy wrap; the caller checks the result before trusting it."""
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if not line or font.getlength(trial) <= width:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


with open(os.path.join(HERE, "land_cache.json")) as _fh:
    GEO_DATA = json.load(_fh)
NORTH = GEO_DATA["lat_top"]
SOUTH = GEO_DATA["lat_bottom"]
RINGS = GEO_DATA["rings"]


def place(lon, lat, frame):
    """Equirectangular projection into the given frame, in supersampled units."""
    left, top, right, bottom = frame
    x = left + (lon + 180.0) / 360.0 * (right - left)
    y = top + (NORTH - lat) / (NORTH - SOUTH) * (bottom - top)
    return x, y


PIN_R = 11.5
DOT_R = 5.5
CARD_H = 108
GUTTER = 17


def geometry():
    """All measurements in one place, derived bottom-up so nothing collides."""
    margin = int(0.036 * PAGE)
    span = PAGE - 2 * margin

    date_pt = 86
    while date_pt > 30 and face(date_pt, serif=True, bold=True).getlength(DAY) > span:
        date_pt -= 1

    fonts = {
        "kick": face(16),
        "date": face(date_pt, serif=True, bold=True),
        "stand": face(25, serif=True),
        "stat": face(14),
        "tag": face(12, bold=True),
        "head": face(28, serif=True, bold=True),
        "detail": face(17),
        "pin": face(15, bold=True),
        "badge": face(18, bold=True),
        "foot_tag": face(13, bold=True),
        "foot": face(16),
    }

    y = margin + 2 * SS
    kick_y = y
    y += 24 * SS
    date_y = y
    y += int(date_pt * 1.12 * SS)
    hair_y = y
    y += 11 * SS
    stand_y = y
    y += 31 * SS
    bar_y = y
    map_top = y + 15 * SS

    foot_rows = (len(FOOTER) + 1) // 2
    foot_h = 21 * SS + foot_rows * 22 * SS
    foot_top = PAGE - margin - foot_h

    cards_h = 3 * CARD_H * SS
    cards_top = foot_top - GUTTER * SS - cards_h
    map_bottom = cards_top - GUTTER * SS
    frame = (margin, map_top, PAGE - margin, map_bottom)

    col_w = span // 2
    text_inset = 27 * SS
    cards = []
    for idx, (field, number, headline, detail, _pt) in enumerate(CARDS):
        cx = margin + (idx % 2) * col_w
        cy = cards_top + (idx // 2) * CARD_H * SS
        usable = col_w - text_inset - 16 * SS
        cards.append({
            "field": field, "number": number, "headline": headline,
            "detail": detail,
            "box": (cx, cy, col_w, CARD_H * SS),
            "badge_xy": (cx + 1 * SS, cy + 6 * SS),
            "text_x": cx + text_inset,
            "text_w": usable,
        })

    return {
        "margin": margin, "span": span, "fonts": fonts, "date_pt": date_pt,
        "kick_y": kick_y, "date_y": date_y, "hair_y": hair_y,
        "stand_y": stand_y, "bar_y": bar_y,
        "frame": frame, "cards": cards, "cards_top": cards_top,
        "cards_h": cards_h, "foot_top": foot_top, "foot_h": foot_h,
        "col_w": col_w, "foot_rows": foot_rows,
        "foot_col": span // 2,
    }


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
        poly = [place(lon, lat, frame) for lon, lat in ring]
        if len(poly) >= 3:
            draw.polygon(poly, fill=GEO, outline=COAST, width=int(1.7 * SS))

    draw.rectangle([left, top, right, bottom], outline=BLACK, width=int(2.3 * SS))


def paint_markers(draw, frame, pin_font):
    radius = PIN_R * SS
    halo = 4 * SS
    for _field, number, _headline, _detail, (lon, lat) in CARDS:
        cx, cy = place(lon, lat, frame)
        draw.ellipse([cx - radius - halo, cy - radius - halo,
                      cx + radius + halo, cy + radius + halo], fill=NEWS)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                     fill=RED, outline=BLACK, width=int(1.0 * SS))
        tw = pin_font.getlength(number)
        draw.text((cx - tw / 2, cy - pin_font.size / 2 - 1.2 * SS), number,
                  font=pin_font, fill=NEWS)

    for lon, lat in SPOTS:
        cx, cy = place(lon, lat, frame)
        r = DOT_R * SS
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=NAVY,
                     outline=NEWS, width=int(1.5 * SS))


def paint_masthead(draw, g):
    f = g["fonts"]
    m = g["margin"]
    spaced(draw, (m, g["kick_y"]), KICKER, f["kick"], GREY, 8.5)
    draw.text((m, g["date_y"]), DAY, font=f["date"], fill=BLACK)
    draw.line([(m, g["hair_y"]), (PAGE - m, g["hair_y"])], fill=BLACK,
              width=int(2.3 * SS))
    draw.text((m, g["stand_y"]), STANDFIRST, font=f["stand"], fill=BLACK)
    stat_w = spaced_width(STAT, f["stat"], 2.6)
    spaced(draw, (PAGE - m - stat_w, g["stand_y"] + 8 * SS), STAT, f["stat"],
           RED, 2.6)
    draw.rectangle([m, g["bar_y"], PAGE - m, g["bar_y"] + 5 * SS], fill=BLACK)


def paint_cards(draw, g):
    f = g["fonts"]
    m = g["margin"]
    # a hairline between the columns, so six cards read as one grid
    seam = m + g["col_w"] - int(9 * SS)
    draw.line([(seam, g["cards_top"] + 4 * SS),
               (seam, g["cards_top"] + g["cards_h"] - 12 * SS)],
              fill=(206, 200, 189), width=int(1.1 * SS))

    for card in g["cards"]:
        cx, cy, _cw, _ch = card["box"]
        bx, by = card["badge_xy"]
        draw.line([(cx, cy), (cx + 22 * SS, cy)], fill=RED, width=int(2.2 * SS))
        r = 10 * SS
        draw.ellipse([bx, by, bx + 2 * r, by + 2 * r], fill=RED)
        bw = f["badge"].getlength(card["number"])
        draw.text((bx + r - bw / 2, by + r - f["badge"].size / 2 - 1.0 * SS),
                  card["number"], font=f["badge"], fill=NEWS)

        tx = card["text_x"]
        spaced(draw, (tx, cy + 3 * SS), card["field"], f["tag"], RED, 1.5)
        draw.text((tx, cy + 19 * SS), card["headline"], font=f["head"],
                  fill=BLACK)
        yy = cy + 60 * SS
        for line in split_lines(card["detail"], f["detail"], card["text_w"]):
            draw.text((tx, yy), line, font=f["detail"], fill=GREY)
            yy += 21 * SS


def paint_footer(draw, g):
    f = g["fonts"]
    m = g["margin"]
    top = g["foot_top"]
    draw.rectangle([m, top, PAGE - m, top + 2.2 * SS], fill=BLACK)

    label_y = top + 9 * SS
    dot_y = label_y + f["foot_tag"].size / 2
    draw.ellipse([m, dot_y - 4.5 * SS, m + 9 * SS, dot_y + 4.5 * SS], fill=NAVY)
    spaced(draw, (m + 17 * SS, label_y), FOOT_LABEL, f["foot_tag"], NAVY, 2.4)

    split = (len(FOOTER) + 1) // 2
    for idx, item in enumerate(FOOTER):
        col, row = (0, idx) if idx < split else (1, idx - split)
        x = m + col * (g["foot_col"] + 24 * SS) + 2 * SS
        y = label_y + 22 * SS + row * 22 * SS
        draw.text((x, y), item, font=f["foot"], fill=GREY)


def render():
    g = geometry()
    page = Image.new("RGB", (PAGE, PAGE), NEWS)
    draw = ImageDraw.Draw(page)

    paint_masthead(draw, g)
    paint_map(draw, g["frame"])
    paint_markers(draw, g["frame"], g["fonts"]["pin"])
    paint_cards(draw, g)
    paint_footer(draw, g)

    # BOX, not LANCZOS: at an exact integer factor it averages each 3x3 block,
    # so hard ink edges get no overshoot ring and small type keeps its weight.
    return page.resize((1024, 1024), Image.BOX)


def probe():
    """Check the geometry that a broken layout would quietly ruin."""
    g = geometry()
    f = g["fonts"]
    frame = g["frame"]
    faults = []

    print("date %dpt -> %.0f of %.0f px"
          % (g["date_pt"], f["date"].getlength(DAY) / SS, g["span"] / SS))
    print("map %.0fx%.0f px at y=%.0f"
          % ((frame[2] - frame[0]) / SS, (frame[3] - frame[1]) / SS,
             frame[1] / SS))

    pts = []
    for _field, number, _headline, _detail, (lon, lat) in CARDS:
        x, y = place(lon, lat, frame)
        pts.append((number, x / SS, y / SS))
        clear = PIN_R + 4
        inside = (frame[0] / SS + clear < x / SS < frame[2] / SS - clear
                  and frame[1] / SS + clear < y / SS < frame[3] / SS - clear)
        print("  pin %s at (%4.0f,%4.0f) %s"
              % (number, x / SS, y / SS, "in frame" if inside else "OUT OF FRAME"))
        if not inside:
            faults.append("pin %s leaves the map frame" % number)

    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            gap = math.dist(pts[i][1:], pts[j][1:])
            if gap < 2 * PIN_R + 2:
                faults.append("pins %s/%s only %.0f px apart"
                              % (pts[i][0], pts[j][0], gap))

    for lon, lat in SPOTS:
        sx, sy = place(lon, lat, frame)
        sx, sy = sx / SS, sy / SS
        for number, px, py in pts:
            if math.dist((sx, sy), (px, py)) < PIN_R + 8:
                faults.append("dot collides with pin %s" % number)

    for card in g["cards"]:
        head_w = f["head"].getlength(card["headline"])
        detail = split_lines(card["detail"], f["detail"], card["text_w"])
        tag_w = spaced_width(card["field"], f["tag"], 1.5)
        used = 60 * SS + len(detail) * 21 * SS
        print("  card %s: head %.0f/%.0f px, detail %d line(s), used %d/%d"
              % (card["number"], head_w / SS, card["text_w"] / SS, len(detail),
                 used / SS, CARD_H))
        if head_w > card["text_w"]:
            faults.append("card %s headline overruns its column" % card["number"])
        if tag_w > card["text_w"]:
            faults.append("card %s label overruns its column" % card["number"])
        if used > CARD_H * SS:
            faults.append("card %s overflows its row" % card["number"])

    widest = max(f["foot"].getlength(t) for t in FOOTER)
    print("footer widest %.0f of %.0f px; map height %.0f px; footer top %.0f"
          % (widest / SS, g["foot_col"] / SS, (frame[3] - frame[1]) / SS,
             g["foot_top"] / SS))
    if widest > g["foot_col"]:
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
    return 0 if size <= 1048576 else 1


if __name__ == "__main__":
    raise SystemExit(main())
