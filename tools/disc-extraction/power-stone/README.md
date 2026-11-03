# Power Stone and Power Stone 2

Dumps:

- `Power Stone v1.020 (1999)(Capcom)(JP)[!][1MB1]` (`.gdi`), release `ps1`
- `Power Stone 2 v2.000 (2000)(Capcom)(JP)[!]` (`.gdi`), release `ps2`

The names and logos are the same in every release, so nothing from these discs
gets a region.

What the scripts found is written up in each game's notes,
[`content/games/power-stone.md`](../../../content/games/power-stone.md) and
[`content/games/power-stone-2.md`](../../../content/games/power-stone-2.md).

## Run

```sh
PS1="path/to/Power Stone v1.020 (1999)(Capcom)(JP)[!][1MB1]"
PS2="path/to/Power Stone 2 v2.000 (2000)(Capcom)(JP)[!]"
OUT=/tmp/power-stone
python3 -E ../common/disc.py "$PS1" $OUT/ps1 /1ST_READ.BIN
python3 -E ../common/disc.py "$PS2" $OUT/ps2 /1ST_READ.BIN
python3 -E vmu.py ps1 $OUT/ps1/1ST_READ.BIN $OUT/out
python3 -E vmu.py ps2 $OUT/ps2/1ST_READ.BIN $OUT/out
python3 -E prep.py $OUT/out $OUT/inbox                # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
