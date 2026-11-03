# Sword of the Berserk: Guts' Rage

Dump: `Sword of the Berserk - Guts' Rage v1.000 (2000)(Eidos)(US)[!]` (`.gdi`).
The archive files these under the Japanese release's title, with region `US` on
what came from this disc.

## Run

```sh
DUMP="path/to/Sword of the Berserk - Guts' Rage v1.000 (2000)(Eidos)(US)[!]"
OUT=/tmp/berserk
python3 -E ../common/disc.py "$DUMP" $OUT/files /LCDIMG.BIN /1ST_READ.BIN
python3 -E lcdimg.py $OUT/files/LCDIMG.BIN $OUT/out     # screens, manifest, contact sheet
python3 -E anims.py $OUT/files/1ST_READ.BIN $OUT/out/animations.json
python3 -E check.py $OUT/out                            # archive vs disc and code
python3 -E prep.py $OUT/out $OUT/inbox                  # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.

## What's on the disc

`/LCDIMG.BIN` holds 40 screens (48×32) and ten 4×5 digits. Each pixel is a byte
and every image is stored mirrored left to right. The table counts 49 entries,
but a 50th follows the last one and the game draws it (the third frame of the
47/48/49 animation).

The routine at `0x8C033034` in `1ST_READ.BIN` draws the VMU screen once per video
frame. It shows a screen when a tick counter, masked to a 16-tick loop, reaches
0, 4, 8 or 12, so frames hold for 4 ticks (67 ms) or 8 (133 ms). That matches the
Flycast captures of Puck, Puck 2 and All OK exactly. Computed calls overlay the
ammo counter's three digits (screens 11–20). Three other routines show screen 7
("Do not touch") once before saving.

| Screens | Hold (ms) | Archive entry |
| --- | --- | --- |
| 3, 4 | 133, 133 | NG |
| 5, 6 | 133, 133 | All OK (captured) |
| 7, 8, 9 | 67, 67, 133 | Do not touch |
| 22, 21, 23 | 67, 67, 133 | Puck |
| 24, 25, 26 | 67, 67, 133 | Puck |
| 27, 28 | 133, 133 | Puck |
| 29, 30, 31 | 67, 67, 133 | Puck |
| 32, 33, 34 | 67, 67, 133 | Puck |
| 35, 36, 37 | 67, 67, 133 | Puck (captured) |
| 38, 39, 40 | 67, 67, 133 | Puck |
| 41, 42, 43 | 67, 67, 133 | Puck 2 (captured) |
| 47, 48, 49 | 67, 67, 133 | Puck |
| 10 | still | Title screen (US logo) |

Screens 0, 1, 2, 44, 45 and 46 are never drawn by any code that calls the draw
routine (`0x8C03C89C` has four callers), so they're marked `unused`. The Japanese
release's title screen isn't on this disc.

## Sprites

Entries 11–20 are the ten 4×5 digits the computed calls draw as the ammo
counter. `prep.py` emits them as sprites, so the importer keeps them at their
own size in `content/sprites/berserk-millennium-falcon-hen-wasurebana-no-sho/`,
titled by entry number. Still to check in the code: which digit each entry is,
which screen the counter goes on, and where (the sprites' `drawnAt`).
