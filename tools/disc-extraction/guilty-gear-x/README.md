# Guilty Gear X

Dump: `Guilty Gear X (Japan)` (Redump, `.cue` and 38 `.bin` tracks;
T-2402M V2.000). The game came out in Japan alone, so everything from it is
`ntsc-j`.

What the script found is written up in the game's notes,
[`content/games/guilty-gear-x.md`](../../../content/games/guilty-gear-x.md).

## Run

```sh
DUMP="path/to/Guilty Gear X (Japan)"
OUT=/tmp/guilty-gear-x
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN /VMICON01.ICO \
  /VMICON02.ICO /VMICON03.ICO
python3 -E vmu.py $OUT/files $OUT/out     # the screen, save icons, contact sheet
pnpm icons:import $OUT/out/inbox
for d in $OUT/out/saves/*/; do pnpm saveicons:import "$d"; done
```

Run the script from this folder; it needs Pillow. It checks the icons against
the archive's and only writes the ones it lacks, one folder each, so each
entry names its own file as its source.
