# Vampire Chronicle for Matching Service

Dump: `Vampire Chronicle for Matching Service (Japan)` (Redump, `.cue` and
three `.bin` tracks).

What the script found is written up in the game's notes,
[`content/games/vampire-chronicle-for-matching-service.md`](../../../content/games/vampire-chronicle-for-matching-service.md).

## Run

```sh
DUMP="path/to/Vampire Chronicle for Matching Service (Japan)"
OUT=/tmp/vampire
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/out   # screens, saves, contact sheet
pnpm icons:import $OUT/out/inbox
pnpm saveicons:import $OUT/out/saves
```

Run the Python script from this folder.
