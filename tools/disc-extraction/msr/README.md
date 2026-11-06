# Metropolis Street Racer

Dump: `MSR - Metropolis Street Racer (Europe) (En,Fr,De,Es) (Rev B)` (Redump,
`.cue` and three `.bin` tracks). The game's program is `MSR.BIN`, not
`1ST_READ.BIN`.

What the script found is written up in the game's notes,
[`content/games/metropolis-street-racer.md`](../../../content/games/metropolis-street-racer.md).

## Run

```sh
DUMP="path/to/MSR - Metropolis Street Racer (Europe) (En,Fr,De,Es) (Rev B)"
OUT=/tmp/msr
python3 -E ../common/disc.py "$DUMP" $OUT/files /MSR.BIN
python3 -E vmu.py $OUT/files/MSR.BIN $OUT/inbox   # 3 screens and the font
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder. Neither needs Pillow.
