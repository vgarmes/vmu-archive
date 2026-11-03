# Shenmue

Scripts: `tools/disc-extraction/shenmue/`.

Dump: `Shenmue - Isshou Yokosuka v1.007 (1999)(Sega)(JP)(Disc 1 of 4)[!][1MB3, 1MB4, 1MB5, 1MM1]`
(`.gdi`). The VMU art is on disc 1. Every entry from it has region `JP`, the
English screens included.

## What's on the disc

The VMU art is one `IWAD` chunk inside `/MISC/COLD.BIN`, in the same format and
under the same 46 names as [Shenmue II's](shenmue-ii.md), so Shenmue II's
`vmu.py` reads it unchanged: a directory of 8-character names, and each entry a
width byte, a height byte and upright rows, high bit first, 1 = lit.

`1ST_READ.BIN` (loaded at `0x8C010000`) tags its buffer `'LCDM'` (near
`0x8C0EA7C8`) and names every entry: the 17 screens and the 9 `WAZA_*` buttons in
a list of 12-byte slots at `0x8C273078`, and the digits through the patterns
`BT_S?` and `BT_L?` at `0x8C28CCE8`. Nothing in the chunk goes unnamed, so none
of it is marked unused.

All 46 bitmaps match, pixel for pixel, the retail art in Second Screen Archive's
[Shenmue VMU collection](https://second-screen-archive.neocities.org/shenmue-vmu),
which reports the same set on all four discs (the `RSM_*` screens on discs 1–3
only). Disc 2 (`(Disc 2 of 4)[!][1M2, 1MB4]`) was checked too: its `COLD.BIN`
decodes to the same 46 entries.

None of the Goodies characters (see [Goodies](#goodies)) are on discs 1 or 2: a
search of every file, gzip members unpacked, for each pose and portrait
(upright, turned, mirrored and inverted) found nothing, while the same search
finds every screen above.

## Screens

17 entries are whole 48×32 screens. Twelve are the same pixels as Shenmue II's
and are filed there, since the archive keeps each picture once: `PK`, `LOAD_*`,
`SAVE_*`, `OK_*`, `NG_*`, `RSM_JP`, `RSM_OK` and `RSM_NG`. The other five are
Shenmue's own:

| Entry      | Shows                               | Archive title         |
| ---------- | ----------------------------------- | --------------------- |
| `SHENMUE`  | 莎木 (Shenmue) logo                 | Title screen          |
| `BT_START` | 70人バトル START!                   | 70 Man Battle start   |
| `BT_COUNT` | 回目 / 人抜き (digits drawn on top) | 70 Man Battle count   |
| `BT_END`   | 70人抜き おめでとう!!               | 70 Man Battle cleared |
| `RSM_US`   | Please Wait / Don't Pull VM Out.    | Please wait           |

Shenmue II reuses the names `BT_*` and `RSM_US` with new art: its battle screens
are in English, and its Please Wait says "Don't Remove the VMU".

The archive's other title screen, the katakana and Latin logo, came from a
European source and isn't in this chunk.

## Sprites

The other 29 entries are art the game draws onto a screen at run time. They're
kept as three sheets, each glyph after the next, left to right:

- `BT_L0`–`BT_L9` (9×22 each): large digits, 0 to 9.
- `BT_S0`–`BT_S9` (5×10 each): small digits, 0 to 9.
- `WAZA_*` (10×14 each): the QTE buttons, in the game's list order: ←, →, A, B,
  X, Y, L, R and the d-pad.

The digits fill `BT_COUNT`'s blank spaces, before 回目 and 人抜き, but where
exactly, and whether any screen animates, wasn't traced.

## Goodies

Shenmue Goodies was part of Shenmue Passport's online service: Winning Cans won
in the game bought VMU animations of its characters, until the service closed on
1 April 2002. They were downloads, so they're on no disc. The archive's come from
the Neoseeker Shenmue wiki's
[Shenmue Goodies](https://shenmue.neoseeker.com/wiki/Shenmue_Goodies) list,
imported with `tools/disc-extraction/shenmue/goodies.py` from a saved copy of
the page.

- 213 animations, each a character's three or so poses. They play at the wiki
  GIFs' timing (190–500 ms a frame), which nobody has checked against the game.
- 4 portraits, the only stills that fill the 48×32 screen: Ryo Hazuki, Ling Sha
  Hua, Ren Wuying and Niao Sun, the characters the Goodies viewer comes with.
- 337 faces, kept as sprites. The wiki shows them either at 32×32 or centred on
  a 48×32 canvas; the canvas is the wiki's, so they're cut back to the drawn
  columns (32, or 33 for seven drawn a column to the left).

Second Screen Archive's
[Shenmue VMU collection](https://second-screen-archive.neocities.org/shenmue-vmu)
holds 207 of these characters, and its pictures are the same: every one of its
animations frame for frame, and 205 of its portraits pixel for pixel (Masaru Aoi
and Toki Aida differ by 5 pixels). It names Ling Sha Hua (Shenhua) and Ren the
other way round from the wiki; the wiki's names agree with the poses.

The archive's Ryo Hazuki entry was made earlier from the collection's preview
GIF, played at its 300 ms inspection pace; it now has the wiki's frames and
timing.
