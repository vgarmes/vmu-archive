# Shenmue II

Scripts: `tools/disc-extraction/shenmue2/`.

Dump: `Shenmue II v1.003 (2001)(Sega)(JP)(Disc 1 of 4)[!][3MM1]` (`.gdi`). The
VMU art is on disc 1. The entries in Japanese get region `ntsc-j`; the English
ones get none, as they're taken to be in every release.

The first game stores its art the same way, under the same names, and twelve of
the screens are pixel for pixel the same; see [Shenmue](shenmue.md).

## What's on the disc

The `/SPRITE/VM_*.GZ` files are not VMU art: they're 512×512 colour textures.

The VMU art is one `IWAD` chunk inside `/MISC/COLD.BIN`, a pack the game loads at
boot. It was found from the code: `1ST_READ.BIN` (loaded at `0x8C010000`)
allocates a buffer tagged `'LCDM'` at `0x8C0C2460` and looks entries up in it by
name (`0x8C0C2420`) from a list at `0x8C22EF68`. Searching the disc for those
names led to `COLD.BIN`. The format is in `vmu.py`: a directory of 8-character
names, and each entry is a width byte, a height byte and upright rows, high bit
first, 1 = lit.

46 entries: 17 are whole 48×32 screens, all of them in the game's lookup list.
The other 29 are sprites the game draws onto a screen at run time, so they're not
imported:

- `BT_L0`–`BT_L9` (9×22) and `BT_S0`–`BT_S9` (5×10): digits for the BT_COUNT
  counter, looked up as `BT_L?` and `BT_S?`
- `WAZA_*` (10×14): the QTE buttons A, B, X, Y, L, R, the d-pad and arrows

| Entry                | Shows                            | Archive title     |
| -------------------- | -------------------------------- | ----------------- |
| `SHENMUE`            | Shenmue II logo                  | Title screen      |
| `PK`                 | ←P K                             | PK                |
| `LOAD_JP`, `LOAD_US` | ロードちゅうです / Now Loading   | Loading           |
| `SAVE_JP`, `SAVE_US` | セーブちゅうです / Now Saving    | Saving            |
| `OK_JP`, `OK_US`     | セーブしゅうりょう! / OK!        | Save complete, OK |
| `NG_JP`, `NG_US`     | セーブしっぱい! / NG!            | Save failed, NG   |
| `RSM_JP`, `RSM_US`   | じゅんびちゅうです / Please Wait | Please wait       |
| `RSM_OK`, `RSM_NG`   | しゅうりょう! / しっぱい!        | Complete, Failed  |
| `BT_START`           | Battle START!                    | Battle start      |
| `BT_COUNT`           | Defeated (digits drawn on top)   | Defeated          |
| `BT_END`             | All Defeated! Congrats!          | All defeated      |

Nothing here animates by itself; whether the game cycles any of these screens
wasn't traced.
