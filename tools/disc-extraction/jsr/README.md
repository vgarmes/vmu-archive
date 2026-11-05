# Jet Set Radio

Dump: `Jet Set Radio (Japan)` (Redump, `.cue` with three `.bin` tracks).
Only the Japanese pieces get region `ntsc-j`; see `prep.py`.

What the scripts found is written up in the game's notes,
[`content/games/jet-set-radio.md`](../../../content/games/jet-set-radio.md).

## Run

```sh
DUMP="path/to/Jet Set Radio (Japan)"
OUT=/tmp/jsr
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN /JETRADIO/SYSOPTION.AFS
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out                 # the game's screens
python3 -E app.py $OUT/files/JETRADIO/SYSOPTION.AFS $OUT/app       # the graffiti viewer
python3 -E prep.py $OUT/out $OUT/app $OUT/inbox                    # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
