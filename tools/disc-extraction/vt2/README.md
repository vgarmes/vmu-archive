# Virtua Tennis 2

Dump: `Virtua Tennis 2 - Sega Professional Tennis (Europe) (En,Ja,Fr,De,Es)`
(Redump, `.cue` and three `.bin` tracks).

What the script found is written up in the game's notes,
[`content/games/virtua-tennis-2.md`](../../../content/games/virtua-tennis-2.md).

## Run

```sh
DUMP="path/to/Virtua Tennis 2 - Sega Professional Tennis (Europe) (En,Ja,Fr,De,Es)"
OUT=/tmp/vt2
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out   # screens, contact sheet
pnpm icons:import $OUT/out/inbox
```

Run the Python script from this folder.
