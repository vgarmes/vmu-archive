# Sonic Shuffle

Dump: `Sonic Shuffle (Japan)` (Redump, `.cue` and three `.bin` tracks).

What the script found is written up in the game's notes,
[`content/games/sonic-shuffle.md`](../../../content/games/sonic-shuffle.md).

## Run

```sh
DUMP="path/to/Sonic Shuffle (Japan)"
OUT=/tmp/sonic-shuffle
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/inbox ../../../public/notes/sonic-shuffle
pnpm icons:import $OUT/inbox
```

`vmu.py` writes the 2 screens and 7 sprites to the inbox, and an example hand
for the notes, `hand.png`, to the third folder (leave it out to skip it).

Run the Python scripts from this folder. Neither needs Pillow.
