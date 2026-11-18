# The image

`render_image.py` draws `entry.png` — one newspaper front page for Wednesday 18
November 2026: masthead, a world map with six numbered pins, six story cards, and
a footer of six further items from the same day.

It runs at build time only. `main.py` at the repository root ships the resulting
PNG and never renders anything, which keeps the entrypoint standard-library and
its output byte-identical across runs.

## Bands

| band | content |
| --- | --- |
| masthead | "18 NOVEMBER 2026", the weekday kicker, a standfirst and a red region count |
| map | equirectangular land outline, six numbered pins, four unnumbered navy dots |
| cards | two columns of three: field label, headline, one or two lines of detail |
| footer | "also on the day" — six further items in two columns |

Pins carry the same numbers as the cards, so the map and the text read as one
object. Each pin sits at the place the story is filed from, not at the outlet's
office: Qeshm, Seoul, Washington, Mexico City, London, Port-au-Prince.

## Why it looks like this

The brief is a single image for one day of news, read by a vision judge at
roughly 300 px across. That governs every choice:

* **The date is the largest thing on the page.** Without it the picture could be
  any day, and it is the first thing legible when the image is small.
* **Six stories, not sixteen.** A headline size that survives a thumbnail beats a
  dense broadsheet nobody can read; the rest of the day goes in the footer, where
  it reads as texture rather than noise.
* **Hard detail on every card.** "Sales double, the board rules out Huang's
  return" is checkable; "markets react to news" is not.
* **Six regions, four continents.** Breadth is the second thing the brief asks
  for, so the six are chosen across the map, not across one wire's front page.
* **Restrained palette.** Near-black ink on warm paper, one red for the pins, one
  navy for everything secondary. Colour marks, it does not decorate.

## Checks

`--probe` re-runs the layout arithmetic and exits non-zero on:

* a pin outside the frame, or two pins closer than the marker radius;
* a headline or field label wider than its column;
* a card whose detail runs past its row;
* a footer item overrunning its column;
* a map too letterboxed to read.

`check_image.py` then measures the finished PNG rather than trusting the layout:
date-band ink versus body ink, land and sea share of the map frame, land/sea at
ten coordinates whose answer is not in doubt (Sahara, Siberia, Kansas, the Amazon,
Alice Springs, the Congo; Atlantic, Pacific, Indian Ocean, Bay of Bengal), a red
pin within a marker radius of each projected centre, and contrast plus ink share
after a 300 px downscale.

## Rendering

Pillow, 3x supersampling, then **box** down to 1024x1024. Box is right here and
Lanczos is not: at an exact integer factor it averages each 3x3 block, so hard
ink edges get no overshoot ring and small type keeps its weight. Two runs produce
identical bytes, verified with `cmp` against the committed file.
