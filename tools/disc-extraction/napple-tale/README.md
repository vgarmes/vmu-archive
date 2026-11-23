# Napple Tale: Arsia in Daydream

Dump: `Napple Tale - Arsia in Daydream (Japan)` (Redump, `.cue` and three
`.bin` tracks; HDR-0079 V1.006). The game came out in Japan alone, so
everything from it is `ntsc-j`.

What the scripts found is written up in the game's notes,
[`content/games/napple-tale-arsia-in-daydream.md`](../../../content/games/napple-tale-arsia-in-daydream.md).

## Run

```sh
DUMP="path/to/Napple Tale - Arsia in Daydream (Japan)"
OUT=/tmp/napple-tale
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out   # screens, font, saves, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox              # sidecars for the importer
pnpm icons:import $OUT/inbox/screens $OUT/inbox/sprites
pnpm saveicons:import $OUT/out/saves
```

Run the Python scripts from this folder.
