# Crazy Taxi 2

Dump: `Crazy Taxi 2 v1.004 (2001)(Sega)(US)[!]` (`.gdi`). The name and logo
are the same in every release, so nothing from this disc gets a region.

What the scripts found is written up in the game's notes,
[`content/games/crazy-taxi-2.md`](../../../content/games/crazy-taxi-2.md).

## Run

```sh
DUMP="path/to/Crazy Taxi 2 v1.004 (2001)(Sega)(US)[!]"
OUT=/tmp/crazytaxi2
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out    # screens, animations, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox                # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
