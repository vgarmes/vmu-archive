# Shenmue II

Dump: `Shenmue II v1.003 (2001)(Sega)(JP)(Disc 1 of 4)[!][3MM1]` (`.gdi`). The
VMU art is on disc 1. Every entry from it has region `ntsc-j`, the English screens
included.

What the scripts found is written up in the game's notes,
[`content/games/shenmue-ii.md`](../../../content/games/shenmue-ii.md).

## Run

```sh
DUMP="path/to/Shenmue II v1.003 (2001)(Sega)(JP)(Disc 1 of 4)[!][3MM1]"
OUT=/tmp/shenmue2
python3 -E ../common/disc.py "$DUMP" $OUT/files /MISC/COLD.BIN
python3 -E vmu.py $OUT/files/MISC/COLD.BIN $OUT/out    # screens, sprites, manifest, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox                 # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
