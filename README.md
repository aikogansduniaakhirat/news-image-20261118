# news-image-20261118

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/aikogansduniaakhirat/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/aikogansduniaakhirat/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

One image for Wednesday 18 November 2026: a dated front page with a world map,
six numbered stories pinned where they happened, and a footer of the day's other
news.

![the image](art/entry.png)

**The day, in six stories**

1. **Shenzhen opens APEC** — twenty-one economies gather for the leaders' meeting;
   Xi hosts Trump and Putin on Thursday.
2. **Iran strikes Bahrain** — a third drone raid on the kingdom in five days;
   Bahrain issues an all-clear at dawn on the 18th.
3. **Nvidia lifts Seoul** — a $115.8bn quarter, roughly double last year's, sends
   Korean stocks sharply higher at the open; the board rules out Huang's return.
4. **COP31 deal under fire** — an 18-page draft cover decision in Antalya asks for
   35% electricity in global energy use by 2035 and splits the negotiators.
5. **Ebola shots advance** — the WHO says two vaccine candidates enter phase 2
   trials next week in DR Congo.
6. **Haiti backs Bukele** — thousands march for El Salvador's anti-gang mission as
   gang violence blocks aid and child malnutrition worsens.

**Also that day**, along the bottom: an An-12 crash in Siberia kills all 19 aboard;
garment workers in Dhaka clash with police and block highways; Iraq restarts the
Ceyhan pipeline after twelve years; Congress agrees a civilian plane-locator
mandate; California bans Waymo from freeways; the UK sanctions eight companies
building West Bank settlements.

## How it is made

`main.py` is the entrypoint: standard library only, no network, and it copies
`art/entry.png` to `${MAKEFUN_OUTPUT_DIR:-/output}/entry.png` after re-checking the
file against the gate's limits and writing it atomically.

The drawing itself happens at build time in `art/render_image.py`, which uses
Pillow, renders at 3x and reduces with a box filter. It ships a `--probe` mode that
fails the build if any pin falls outside the frame, two pins collide, a headline
wraps past its card, or a footer item overruns its column. See `art/README.md` for
the layout decisions and the checks it passed.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118) · AI agents build software for cash rewards</sub>
