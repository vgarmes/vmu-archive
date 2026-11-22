# Border Down

Dump: `Border Down (Japan)` (Redump, `.cue` and three `.bin` tracks; T-46703M
V1.000). The game came out in Japan alone, so everything from it is `ntsc-j`.

What the scripts found is written up in the game's notes,
[`content/games/border-down.md`](../../../content/games/border-down.md).

## Run

```sh
DUMP="path/to/Border Down (Japan)"
OUT=/tmp/border-down
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out   # screens, digits, save, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox              # sidecars for the importer
pnpm icons:import $OUT/inbox/screens $OUT/inbox/sprites   # screens first
pnpm saveicons:import $OUT/out/saves
```

Run the Python scripts from this folder.
