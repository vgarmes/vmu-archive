# Cool Cool Toon

Dump: `Cool Cool Toon (Japan)` (Redump, `.cue` and three `.bin` tracks;
T-3106M V1.012). The game came out in Japan alone, so everything from it is
`ntsc-j`.

What the scripts found is written up in the game's notes,
[`content/games/cool-cool-toon.md`](../../../content/games/cool-cool-toon.md).

## Run

```sh
DUMP="path/to/Cool Cool Toon (Japan)"
OUT=/tmp/cool-cool-toon
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN /CCT/VM_ICON_BOY.HBN \
  /CCT/VM_ICON_GIRL.HBN /CCT/VM_ICON_MAN.HBN /CCT/VM_ICON_WOMAN.HBN
python3 -E vmu.py $OUT/files $OUT/out     # screens, save icons, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox   # sidecars for the importer
pnpm icons:import $OUT/inbox
pnpm saveicons:import $OUT/out/saves
```

Run the Python scripts from this folder. `vmu.py` checks the man's icon
against the archive's and only writes the other three. The save importer
takes one source for a folder, so each new entry's `source.file` was then
set to its own `/CCT/VM_ICON_*.HBN`.
