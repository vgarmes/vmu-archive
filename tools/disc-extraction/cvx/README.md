# Resident Evil Code: Veronica

Dump: `Biohazard - Code - Veronica (Japan) (Disc 1)` (Redump, `.cue` and
three `.bin` tracks). The title screen says BIOHAZARD, so it's kept as
`ntsc-j`; the other screens get no region.

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

Run the Python scripts from this folder. Neither needs Pillow.
