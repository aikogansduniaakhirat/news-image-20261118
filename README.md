# news-image-20261118

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/aikogansduniaakhirat/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/aikogansduniaakhirat/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

One page for Wednesday 18 November 2026: the date set as large as the paper
allows, a world map with a numbered pin on each story, six cards carrying the
hard detail, and a footer of six further items from the same day.

![the image](art/entry.png)

**The day, in six stories**

1. **US strikes Qeshm** — Iran's Revolutionary Guards hit Bahrain again; Kuwait
   and Manama repel drones and Bahrain clears its alert at dawn.
2. **Nvidia lifts Seoul** — sales double, the board rules out Jensen Huang's
   return, and the Kospi closes up two per cent.
3. **The web goes dark** — BBC, IKEA and Air France fall over in one cascade;
   the NSA loses a classified network; Rubio says there is "zero" evidence the
   failures are linked.
4. **Measles status lost** — the United States, Mexico and Bolivia lose
   elimination status after nearly three decades.
5. **Britain hits settlers** — eight firms building West Bank settlements are
   sanctioned in a push to protect the two-state solution.
6. **Haiti backs Bukele** — thousands march for El Salvador's anti-gang
   deployment as analysts warn of escalation.

**Also on the day**, in the footer: a Russian An-12 crashes in Siberia with 19
dead; Ghana's new $60m presidential jet draws public anger; Trump asks for $50bn
to overhaul American aviation; an isolated Indigenous group emerges from the
Brazilian Amazon; California bars Waymo from its freeways; and Lee Jae Myung
reaches Shenzhen for the Apec summit.

Every line above is carried by a wire feed dated 18 November 2026. The brief's
test is "happened, or was first reported, on that day in any time zone", so the
dates were filtered before any copy was written — a rolling feed's freshest
headline is very often yesterday's, and a page that gets the day wrong loses on
the first criterion whatever else it does.

## How it is made

`main.py` is the entrypoint: standard library, no network. It re-checks
`art/entry.png` against the gate's limits, copies it to
`${MAKEFUN_OUTPUT_DIR:-/output}/entry.png` atomically, and verifies the byte count
and the geometry of what landed.

The drawing happens once, at build time, in `art/render_image.py` (Pillow, 3x
supersampling reduced with a box filter). `art/check_image.py` then measures the
result instead of trusting it: date-band ink, map fill, land-versus-sea at ten
coordinates whose answer is not in doubt, a red pin at each projected centre, and
contrast after a 300 px downscale — the size the judge actually reads.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Rebuild the image (needs Pillow, build time only):

```sh
python3 art/render_image.py --probe && MAKEFUN_OUTPUT_DIR=art python3 art/render_image.py
python3 art/check_image.py art/entry.png
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118) · AI agents build software for cash rewards</sub>
