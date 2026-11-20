# Capcom vs. SNK: Millennium Fight 2000

Dump: `Capcom vs. SNK - Millennium Fight 2000 (Japan) (Rev A)` (Redump, `.cue`
and three `.bin` tracks).

What the script found is written up in the game's notes,
[`content/games/capcom-vs-snk-millennium-fight-2000.md`](../../../content/games/capcom-vs-snk-millennium-fight-2000.md).

## Run

```sh
DUMP="path/to/Capcom vs. SNK - Millennium Fight 2000 (Japan) (Rev A)"
OUT=/tmp/cvs
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out   # screens, contact sheet
pnpm icons:import $OUT/out/inbox
```

Run the Python script from this folder.
