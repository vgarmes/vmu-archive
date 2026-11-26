# Grandia II

Dumps: `Grandia II (Japan)` (Redump, `.cue` and three `.bin` tracks; T-4503M
V1.001) and `Grandia II (Europe)` (Redump, `.cue` and five `.bin` tracks;
T-17715D V1.000).

What the script found is written up in the game's notes,
[`content/games/grandia-2.md`](../../../content/games/grandia-2.md).

## Run

```sh
DUMP="path/to/Grandia II (Japan)"    # or (Europe), with eu below
OUT=/tmp/grandia-2-jp
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN \
  /BIN/GR2TITLE.BIN /BIN/FIELD.BIN
python3 -E vmu.py jp $OUT/files $OUT/out     # the four screens, contact sheet
pnpm icons:import $OUT/out/inbox
```

Run the script from this folder; it needs Pillow. The European disc's NG and
OK are the Japanese disc's, so the importer skips them as duplicates.
