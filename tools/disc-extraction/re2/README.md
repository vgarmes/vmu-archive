# Resident Evil 2

Dump: `Resident Evil 2 (Europe) (En,Fr) (Disc 1)` (Redump, `.cue` and six
`.bin` tracks; T-7004D-50 V1.000).

What the script found is written up in the game's notes,
[`content/games/resident-evil-2.md`](../../../content/games/resident-evil-2.md).

## Run

```sh
DUMP="path/to/Resident Evil 2 (Europe) (En,Fr) (Disc 1)"
OUT=/tmp/re2
python3 -E ../common/disc.py "$DUMP" $OUT/files /BIO2DC.EXE
python3 -E vmu.py $OUT/files/BIO2DC.EXE $OUT/out   # screens, sprites, save icons, contact sheet
pnpm icons:import $OUT/out/inbox
for d in $OUT/out/saves/*/; do pnpm saveicons:import "$d"; done
```

Run the script from this folder; it needs Pillow. It checks the save icons
against the archive's and only writes the ones it lacks, one folder each.
