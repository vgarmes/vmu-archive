# Resident Evil Code: Veronica

Dumps: `Biohazard - Code - Veronica (Japan) (Disc 1)` and `Resident Evil -
Code - Veronica (Europe) (Disc 1)` (Redump, `.cue` and three `.bin` tracks).
Both scripts tell the two programs apart by themselves. The European program
only adds its title; the importer skips the other screens as duplicates.

What the scripts found is written up in the game's notes,
[`content/games/resident-evil-code-veronica.md`](../../../content/games/resident-evil-code-veronica.md).

## Run

```sh
DUMP="path/to/Biohazard - Code - Veronica (Japan) (Disc 1)"
OUT=/tmp/cvx
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/inbox   # screens, redrawn from the sheet
pnpm icons:import $OUT/inbox
python3 -E saves.py $OUT/files/1ST_READ.BIN            # checks the archive's save icons
```

For the European disc, the same with its dump and another `OUT`.

Run the Python scripts from this folder. Neither needs Pillow.
