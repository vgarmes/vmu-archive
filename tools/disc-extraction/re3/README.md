# Resident Evil 3: Nemesis

Dump: `Biohazard 3 - Last Escape (Japan)` (Redump, `.cue` and three `.bin`
tracks; T-1222M V1.002).

What the scripts found is written up in the game's notes,
[`content/games/resident-evil-3-nemesis.md`](../../../content/games/resident-evil-3-nemesis.md).

## Run

```sh
DUMP="path/to/Biohazard 3 - Last Escape (Japan)"
OUT=/tmp/re3
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN /RETENUTO/DC/VMS_1.DCL \
  /RETENUTO/DC/BIO3_FICON.DCB /RETENUTO/DC/BIO3_SYSFICON.DCB
python3 -E vmu.py $OUT/files $OUT/out     # screens and sidecars, contact sheet
pnpm icons:import $OUT/out/inbox
python3 -E saves.py $OUT/files            # checks the archive's save icons
```

Run the Python scripts from this folder. `vmu.py` needs Pillow; `saves.py`
doesn't.
