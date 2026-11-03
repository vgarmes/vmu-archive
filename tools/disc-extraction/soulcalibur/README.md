# Soul Calibur

Dump: `Soul Calibur v1.000 (1999)(Namco)(US)[!][1S]` (`.gdi`). The chibis are
the same in every release, so nothing from this disc gets a region.

What the scripts found is written up in the game's notes,
[`content/games/soul-calibur.md`](../../../content/games/soul-calibur.md).

## Run

```sh
DUMP="path/to/Soul Calibur v1.000 (1999)(Namco)(US)[!][1S]"
OUT=/tmp/soulcalibur
python3 -E vmu.py "$DUMP" $OUT/out       # reads HUMAN.DAT straight from the dump
python3 -E prep.py $OUT/out $OUT/inbox
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
