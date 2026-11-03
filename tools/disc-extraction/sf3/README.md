# Street Fighter III 3rd Strike

Dump: `Street Fighter III 3rd Strike - Fight for the Future v1.003 (2000)(Capcom)(JP)[!]`
(`.gdi`). The archive files these under `Street Fighter III: 3rd Strike`, with no
region: the name and logo are the same in every release.

What the scripts found is written up in the game's notes,
[`content/games/street-fighter-iii-3rd-strike.md`](../../../content/games/street-fighter-iii-3rd-strike.md).

## Run

```sh
DUMP="path/to/Street Fighter III 3rd Strike - Fight for the Future v1.003 (2000)(Capcom)(JP)[!]"
OUT=/tmp/sf3
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out    # screens, manifest, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox                # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
