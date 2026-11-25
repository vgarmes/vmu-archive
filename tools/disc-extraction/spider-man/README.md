# Spider-Man

Dump: `Spider-Man (USA)` (Redump, `.cue` and five `.bin` tracks).

What the script found is written up in the game's notes,
[`content/games/spider-man.md`](../../../content/games/spider-man.md).

## Run

```sh
DUMP="path/to/Spider-Man (USA)"
OUT=/tmp/spider-man
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN /VMULOGO.BMP \
  /VMUSAVE.BMP /VMULOAD.BMP /VMUOK.BMP /VMUFAILED.BMP
python3 -E vmu.py $OUT/files $OUT/out     # the five screens, contact sheet
pnpm icons:import $OUT/out/inbox
```

Run the script from this folder; it needs Pillow.
