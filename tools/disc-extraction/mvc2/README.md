# Marvel vs. Capcom 2

Dump: `Marvel vs. Capcom 2 - New Age of Heroes (Japan)` (Redump, `.cue` and
three `.bin` tracks). The logo is the same in every release, so its screens get
no region; the save icons it adds are kept as `JP`, as their names are.

What the scripts found is written up in the game's notes,
[`content/games/marvel-vs-capcom-2.md`](../../../content/games/marvel-vs-capcom-2.md).

## Run

```sh
DUMP="path/to/Marvel vs. Capcom 2 - New Age of Heroes (Japan)"
OUT=/tmp/mvc2
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN /VS4.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/files/VS4.BIN $OUT/out   # screens, saves, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox                                 # screens to import
pnpm icons:import $OUT/inbox
pnpm saveicons:import $OUT/out/saves                                    # save icons
python3 -E vscom.py $OUT/files/VS4.BIN $OUT/vscom                      # the VS.COM VMU program
pnpm icons:import $OUT/vscom/inbox
```

Run the Python scripts from this folder.
