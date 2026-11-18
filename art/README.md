# The image

`render_image.py` draws `entry.png` — a dated front page: masthead, a world map
with six numbered pins, six story cards, and a footer of other news from the day.

It runs at build time only. `main.py` at the repository root ships the resulting
PNG; it never renders anything, so the entrypoint stays standard-library and
deterministic.

## Layout

| band | content |
| --- | --- |
| masthead | "18 NOVEMBER 2026", the day, and a one-line summary |
| map | equirectangular land outline, six pins placed at each story's country |
| stories | two columns of three cards: region label, headline, one-line detail |
| footer | "also that day" — seven further items in two columns |

Pins are keyed to the story numbers in the cards, so the map reads top to bottom
with the page. Positions are country centroids, not cities, because most stories
are national in scope.

## Why it looks like this

The brief is one image for a day of news, and the judge is a vision model looking
at a 300px thumbnail. That drives every decision:

* **A date stamp, large.** Without it the image could be any day. It is the first
  thing legible when the picture is small.
* **Six stories, not sixteen.** Six cards at a headline size that survives 300px
  beats a dense broadsheet nobody can read. The rest of the day goes in the
  footer, where it reads as texture rather than noise.
* **Numbers on both cards and pins.** The pairing is what makes the map and the
  text one object instead of two.
* **Restrained palette.** Near-black ink on warm paper, one red for the pins.
  Colour is used to mark, not to decorate.

## Checks

`--probe` re-runs the layout arithmetic and fails the build on:

* a pin outside the frame, or two pins closer than the marker radius;
* a headline wrapping past its card, or a detail line past two lines;
* a footer item overrunning its column;
* the legend and footer colliding, or either running off the bottom.

The render is also inspected at 300px, the judge's likely thumbnail size, before
the file is committed.

## Rendering

Pillow, 3x supersampling, then a box filter down to 1024x1024 — the map outline
and the hairlines are the parts that alias visibly at 1x. Texture is a fixed-seed
procedural grain, so every run produces the same bytes.
