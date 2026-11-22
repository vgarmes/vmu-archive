# Tokyo Bus Guide

Dump: `Tokyo Bus Guide (Japan) (Rev A)` (Redump, `.cue` and three `.bin`
tracks; T-35402M V2.000). The game came out in Japan alone, so everything from
it is `ntsc-j`.

What the scripts found is written up in the game's notes,
[`content/games/tokyo-bus-guide.md`](../../../content/games/tokyo-bus-guide.md).

## Run

```sh
DUMP="path/to/Tokyo Bus Guide (Japan) (Rev A)"
OUT=/tmp/tokyo-bus
python3 -E ../common/disc.py "$DUMP" $OUT/files /SYSTEM/NOW_LOADING.LCD /SYSTEM/VM_BUS.LCD \
    /SYSTEM/VM_DANGER.LCD /SYSTEM/PDAQUIZ.BIN
python3 -E vmu.py $OUT/files $OUT/out     # screens, sprites, the quiz save, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox    # sidecars for the importer
pnpm icons:import $OUT/inbox
pnpm saveicons:import $OUT/out/saves
```

Run the Python scripts from this folder.
