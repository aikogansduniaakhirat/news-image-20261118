# news-image-20261118

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/aikogansduniaakhirat/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/aikogansduniaakhirat/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

One image for Wednesday 18 November 2026: a dated front page with a world map,
six numbered stories pinned where they happened, and a footer of the day's other
news.

![the image](art/entry.png)

**The day, in six stories**

1. **US strikes Qeshm** — after Iran's Guards hit Bahrain again; Manama issues
   an all-clear at dawn on the 18th.
2. **Nvidia lifts Seoul** — revenue doubles, the board rules out Huang's return,
   and Korean stocks open sharply higher.
3. **Outages hit the web** — BBC, IKEA and Air France go down as Trump calls the
   string of failures "fine"; the NSA loses a classified network.
4. **Measles status lost** — the US, Mexico and Bolivia lose elimination after
   nearly three decades.
5. **UK targets settlers** — eight firms building West Bank settlements are
   sanctioned in a push to protect the two-state solution.
6. **Haiti backs Bukele** — thousands march for El Salvador's anti-gang mission
   as analysts warn of escalation.

**Also that day**, along the bottom: a Russian An-12 crashes in Siberia, killing
19; Trump asks for $50bn to overhaul US aviation; Congress agrees a civilian
plane-locator mandate; California bans Waymo from freeways; the Knesset gets a
new speaker from the Eisenkot bloc; and Lee Jae Myung reaches Shenzhen for APEC.

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
