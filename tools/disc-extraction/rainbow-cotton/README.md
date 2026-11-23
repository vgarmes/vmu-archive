# Rainbow Cotton

Dump: `Rainbow Cotton (Japan)` (Redump, `.cue` and three `.bin` tracks; T-9901M
V1.009). The game came out in Japan alone, so everything from it is `ntsc-j`.

What the scripts found is written up in the game's notes,
[`content/games/rainbow-cotton.md`](../../../content/games/rainbow-cotton.md).

## Run

```sh
DUMP="path/to/Rainbow Cotton (Japan)"
OUT=/tmp/rainbow-cotton
python3 -E ../common/disc.py "$DUMP" $OUT/files /TITLE.BIN /GAME.BIN /BO01.BIN /LAST.BIN
python3 -E vmu.py $OUT/files $OUT/out     # screens, animations, save icon check, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox   # sidecars for the importer
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder. The save icon is already in the
archive; `vmu.py` checks it against the program.
