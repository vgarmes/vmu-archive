# Sakura Taisen 3: Paris wa Moete Iru ka

Dump: `Sakura Taisen 3 - Paris wa Moete Iru Ka v1.003 (2001)(Sega)(JP)(Disc 1 of 3)[!][3M1]`
(`.gdi`). Every entry from it has region `JP`.

What the scripts found is written up in the game's notes,
[`content/games/sakura-taisen-3-paris-wa-moete-iru-ka.md`](../../../content/games/sakura-taisen-3-paris-wa-moete-iru-ka.md).

## Run

```sh
DUMP="path/to/Sakura Taisen 3 - Paris wa Moete Iru Ka v1.003 (2001)(Sega)(JP)(Disc 1 of 3)[!][3M1]"
OUT=/tmp/sakura3
python3 -E ../common/disc.py "$DUMP" $OUT/files /ADVDATA/SYSTEM.LC1 \
  /MINIGAME/KAJINO1.LC1 /MINIGAME/KAJINO2.LC1 /MINIGAME/KAJINO3.LC1 \
  /MINIGAME/MGBJ.BIN /MINIGAME/MGERK.BIN /MINIGAME/MGGRI.BIN /MINIGAME/MGHAN.BIN \
  /MINIGAME/MGKG_COQ.LC1 /MINIGAME/MGKG_ERI.LC1 /MINIGAME/MGKG_GLY.LC1 \
  /MINIGAME/MGKG_HAN.LC1 /MINIGAME/MGKG_OGA.LC1 /MINIGAME/MGKG_ROB.LC1 \
  /MINIGAME/MGKOK.BIN /MINIGAME/MGKT.BIN /MINIGAME/MGPOK.BIN /MINIGAME/MGROB.BIN \
  /MINIGAME/MGRU.BIN /MINIGAME/MGSLOT.BIN \
  /SLG/UNITS/BOSS_CROW_N.BC /SLG/UNITS/BOSS_LION_N.BC /SLG/UNITS/BOSS_RABBIT_N.BC \
  /SLG/UNITS/BOSS_SCORPION_N.BC /SLG/UNITS/BOSS_SNAKE_N.BC \
  /SLG/UNITS/COQUELICOT_F1_N.BC /SLG/UNITS/ERICA_F1_N.BC /SLG/UNITS/GLYCINE_F1_N.BC \
  /SLG/UNITS/HANABI_F1_N.BC /SLG/UNITS/LOBELIA_F1_N.BC \
  /SLG/UNITS/OGAMI_F1A_N.BC /SLG/UNITS/OGAMI_F1B_N.BC /SLG/UNITS/OGAMI_F1C_N.BC \
  /SLG/G01/SMAP01.ESM
python3 -E vmu.py $OUT/files $OUT/out     # every entry, manifest, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox    # PICKS, ANIMS, BLINKS, BANNERS and SPRITES
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.
