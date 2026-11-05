# Moero! Justice Gakuen

Dump: `Moero! Justice Gakuen v1.004 (2000)(Capcom)(JP)[!][1M4]` (`.gdi`). The
archive files these under `Project Justice`. The disc carries both the Japanese
and the English (Project Justice) screens, so region follows the logo: `ntsc-j` on
the Japanese pair, none on the Project Justice pair, which was the US and
European title.

What the scripts found is written up in the game's notes,
[`content/games/project-justice.md`](../../../content/games/project-justice.md).

## Run

```sh
DUMP="path/to/Moero! Justice Gakuen v1.004 (2000)(Capcom)(JP)[!][1M4]"
OUT=/tmp/justice
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out    # screens, manifest, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox                # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
