# Bakuretsu Muteki Bangaioh

Dump: `Bakuretsu Muteki Bangaioh v1.003 (1999)(ESP)(JP)[!]` (`.gdi`). The archive
files these under `Bangai-O`. Only the katakana title screen gets region
`ntsc-j`; the rest is English text or the Treasure logo, so it has none.

What the scripts found is written up in the game's notes,
[`content/games/bangai-o.md`](../../../content/games/bangai-o.md).

## Run

```sh
DUMP="path/to/Bakuretsu Muteki Bangaioh v1.003 (1999)(ESP)(JP)[!]"
OUT=/tmp/bangaioh
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out    # screens, scripts, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox                # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
