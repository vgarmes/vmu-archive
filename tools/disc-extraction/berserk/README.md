# Sword of the Berserk: Guts' Rage

Dump: `Sword of the Berserk - Guts' Rage v1.000 (2000)(Eidos)(US)[!]` (`.gdi`).
The archive files these under the Japanese release's title, with region `US` on
what came from this disc.

What the scripts found is written up in the game's notes,
[`content/games/berserk-millennium-falcon-hen-wasurebana-no-sho.md`](../../../content/games/berserk-millennium-falcon-hen-wasurebana-no-sho.md).

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
