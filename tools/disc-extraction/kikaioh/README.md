# Choukou Senki Kikaioh

Dump: Redump `Choukou Senki Kikaioh (Japan)` (`.cue`), T-1206M, V1.003. The
archive files it under Tech Romancer.

- `vmu.py` decodes the game's two screens from `1ST_READ.BIN`.
- `mini.py` extracts Kikaioh Mini, the VMU game in `/GAME/KIKAIOH.BIN`, and its
  screens.

What the scripts found is written up in the game's notes,
[`content/games/tech-romancer.md`](../../../content/games/tech-romancer.md).

## Run

```sh
DUMP="path/to/Choukou Senki Kikaioh (Japan)"
OUT=/tmp/kikaioh
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN /GAME/KIKAIOH.BIN
python3 -E vmu.py $OUT/files/1ST_READ.BIN $OUT/main
python3 -E mini.py $OUT/files/GAME/KIKAIOH.BIN $OUT/mini
pnpm icons:import $OUT/main/inbox
pnpm icons:import $OUT/mini/inbox
```

Run the Python scripts from this folder.
