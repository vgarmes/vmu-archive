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

## Power Stone Mini

`mini.py` extracts the VMU game Power Stone carries in its `1ST_READ.BIN`, and
its art. It was run on the Redump dump `Power Stone (Japan)` (`.cue`), which is
the same build as v1.020 above: the title and ACCESS screens sit at the same
offsets, byte for byte.

```sh
PS1="path/to/Power Stone (Japan)"
python3 -E ../common/disc.py "$PS1" $OUT/ps1 /1ST_READ.BIN
python3 -E mini.py $OUT/ps1/1ST_READ.BIN $OUT/mini   # PSMINI.VMS, inbox/, notes/, contact sheet
pnpm icons:import $OUT/mini/inbox
cp $OUT/mini/notes/*.gif ../../../public/notes/power-stone/   # the notes' portrait GIFs
```

To read the VMU program's code: `python3 -E ../common/lc86k.py $OUT/mini/PSMINI.VMS <hex address>`.
