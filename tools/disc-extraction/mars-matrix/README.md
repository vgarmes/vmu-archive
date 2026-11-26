# Mars Matrix

Dump: `Mars Matrix (Japan)` (Redump, `.cue` and three `.bin` tracks; T-1238M
V1.000).

What the script found is written up in the game's notes,
[`content/games/mars-matrix.md`](../../../content/games/mars-matrix.md).

## Run

```sh
DUMP="path/to/Mars Matrix (Japan)"
OUT=/tmp/mars-matrix
python3 -E ../common/disc.py "$DUMP" $OUT/files /00MMXDC.BIN
python3 -E vmu.py $OUT/files $OUT/out     # the six screens, contact sheet
pnpm icons:import $OUT/out/inbox
```

Run the script from this folder; it needs Pillow.
