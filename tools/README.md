# Profile build tools

Every SVG in `../assets` is generated here. Never hand-edit them: fonts, images and animation timelines are base64 and
keyTimes. Edit `profile_kit/content.py` (all personal text and data) and rebuild.

## Setup

```bash
python -m pip install -r tools/requirements.txt
python -m playwright install chromium      # only for verify.py and the browser tests
```

## Build

```bash
python tools/build.py                       # all six SVGs into assets/
python tools/build.py --only hero           # one file
python tools/build.py --only hero --video path/to/wave.mp4   # play YOUR clip in the viewfinder
python tools/build.py --refresh             # re-pull repos, stars and commits first (set GITHUB_TOKEN)
```

`--video` embeds **every** frame of the clip as a JPEG (resolution and quality adapt to a size budget; raise it with
`--hero-kb 900`). Without `--video` the viewfinder plays a stand-in push-in built from `media/office.png`.
`--refresh` also re-reads every commit date through metadata-only `git clone`s, which feeds `contribute.svg`.

## Verify

```bash
python tools/verify.py assets/hero.svg --times 0 0.5 1 2 3 3.7 --out /tmp/renders          # seek the timeline
python tools/verify.py assets/hero.svg --static --out /tmp/renders                         # animation stripped (finished card)
python -m pytest tests -q
```

## Design rules the build enforces

* CSS and SMIL only; nothing loaded from the network; fonts are subset WOFF2, images are PNG (stills) or JPEG (video frames).
* Base attributes are the finished state. CSS entrances use `animation-fill-mode: both`; every SMIL timeline starts at `0s`
  and encodes delays in `keyTimes`, so a renderer that ignores animation still shows a complete card.
* Ids are namespaced per file (`hero-`, `ab-`, `st-`, `id-`, `cn-`, `co-`).
* Dashes use measured lengths, never `pathLength`, which some engines ignore on shapes.
* Bump the `?v=` number in the root README whenever an SVG changes (it is `?v=2` now).

## Changing assets

`prepare_assets.py` re-extracts fonts and Simple Icons paths from npm (and adds hand-drawn LinkedIn, Matplotlib and Antigravity marks,
which Simple Icons does not ship); `prepare_assets.py --measure` re-measures the line-icon lengths in a browser. It re-extracts fonts and Simple Icons paths from npm (`simple-icons`, `@fontsource/azeret-mono`,
`@fontsource-variable/bricolage-grotesque`); the extracted results are committed so a normal build needs no Node.
