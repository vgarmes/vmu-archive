# Shenmue

Dump: `Shenmue - Isshou Yokosuka v1.007 (1999)(Sega)(JP)(Disc 1 of 4)[!][1MB3, 1MB4, 1MB5, 1MM1]`
(`.gdi`). The entries in Japanese get region `ntsc-j`; the English ones get
none, as they're taken to be in every release.

The art is stored the way Shenmue II stores it, so Shenmue II's
[`vmu.py`](../shenmue2/vmu.py) decodes it unchanged; only `prep.py` is this
game's own.

What the scripts found is written up in the game's notes,
[`content/games/shenmue.md`](../../../content/games/shenmue.md).

## Run

```sh
DUMP="path/to/Shenmue - Isshou Yokosuka v1.007 (1999)(Sega)(JP)(Disc 1 of 4)[!][1MB3, 1MB4, 1MB5, 1MM1]"
OUT=/tmp/shenmue
python3 -E ../common/disc.py "$DUMP" $OUT/files /MISC/COLD.BIN
python3 -E ../shenmue2/vmu.py $OUT/files/MISC/COLD.BIN $OUT/out   # screens, sprites, manifest, contact sheet
python3 -E prep.py $OUT/out $OUT/inbox                            # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.

## Passport disc

The Goodies viewer, `/PASSPORT/ATU/SYEN.BIN`, is on disc 4:
`Shenmue - Isshou Yokosuka v1.007 (1999)(Sega)(JP)(Disc 4 of 4)[!][30M2][Passport v1.010]`.

```sh
DUMP4="path/to/Shenmue - Isshou Yokosuka v1.007 (1999)(Sega)(JP)(Disc 4 of 4)[!][30M2][Passport v1.010]"
python3 -E ../common/disc.py "$DUMP4" $OUT/files4 /PASSPORT/ATU/SYEN.BIN
python3 -E passport.py $OUT/files4/PASSPORT/ATU/SYEN.BIN $OUT/passport-inbox
pnpm icons:import $OUT/passport-inbox
```

## Goodies

The downloadable characters aren't on any disc. `goodies.py` reads Neoseeker's
[Shenmue Goodies](https://shenmue.neoseeker.com/wiki/Shenmue_Goodies) page,
saved from a browser as "Webpage, Complete" (the `.html` and its `_files`
folder):

```sh
python3 -E goodies.py "path/to/Shenmue Goodies - Shenmue Wiki - Neoseeker.html" $OUT/goodies-inbox
pnpm icons:import $OUT/goodies-inbox
```
