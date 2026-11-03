# Ikaruga

Dump: `Ikaruga v1.002 (2002)(ESP)(JP)[!]` (`.gdi`). The archive's entries have
no region: the logo and the English text are the same in every release.

What the scripts found is written up in the game's notes,
[`content/games/ikaruga.md`](../../../content/games/ikaruga.md).

## Run

```sh
DUMP="path/to/Ikaruga v1.002 (2002)(ESP)(JP)[!]"
OUT=/tmp/ikaruga
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out    # screens, digits, manifest, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox                # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
