# Space Channel 5: Part 2

Dump: `Space Channel 5 Part 2 (Japan)` (Redump, `.cue` and three `.bin`
tracks; HDR-0190 V2.000). The Dreamcast release was Japan's alone, so
everything from it is `ntsc-j`.

What the scripts found is written up in the game's notes,
[`content/games/space-channel-5-part-2.md`](../../../content/games/space-channel-5-part-2.md).

## Run

```sh
DUMP="path/to/Space Channel 5 Part 2 (Japan)"
OUT=/tmp/space-channel-5-part-2
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out   # screens, save icon check, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox              # sidecars for the importer
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder. The save icon is already in the
archive; `vmu.py` checks it against the program.
