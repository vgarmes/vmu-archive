# Shinseiki Evangelion: Typing E-Keikaku

Dump: `Shinseiki Evangelion - Typing E Keikaku v1.001 (2001)(Gainax)(JP)[!][req. keyboard]`
(`.gdi`). Every entry from it has region `ntsc-j`.

What the scripts found is written up in the game's notes,
[`content/games/shinseiki-evangelion-typing-e-keikaku.md`](../../../content/games/shinseiki-evangelion-typing-e-keikaku.md).

## Run

```sh
DUMP="path/to/Shinseiki Evangelion - Typing E Keikaku v1.001 (2001)(Gainax)(JP)[!][req. keyboard]"
OUT=/tmp/eva-typing
python3 -E ../common/disc.py "$DUMP" $OUT/files /TYPE_E.EXE
python3 -E vmu.py $OUT/files/TYPE_E.EXE $OUT/out    # screens, manifest, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox              # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
