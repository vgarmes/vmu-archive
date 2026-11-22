# Super Puzzle Fighter II X for Matching Service

Dump: `Super Puzzle Fighter II X for Matching Service (Japan)` (Redump, `.cue`
and three `.bin` tracks; T-1250M V1.001). The game came out in Japan alone, so
everything from it is `ntsc-j`.

What the scripts found is written up in the game's notes,
[`content/games/super-puzzle-fighter-ii-x-for-matching-service.md`](../../../content/games/super-puzzle-fighter-ii-x-for-matching-service.md).

## Run

```sh
DUMP="path/to/Super Puzzle Fighter II X for Matching Service (Japan)"
OUT=/tmp/spf2x
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out   # screens, saves, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox              # screens to import
pnpm icons:import $OUT/inbox
pnpm saveicons:import $OUT/out/saves                # save icons
```

Run the Python scripts from this folder.
