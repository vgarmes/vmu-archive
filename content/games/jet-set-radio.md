# Jet Set Radio

Scripts: `tools/disc-extraction/jsr/`.

Dump: `Jet Set Radio (Japan)` (Redump). The VMU art has two homes: the game's
own screens in `1ST_READ.BIN`, and a whole VMU program, the graffiti viewer,
that the game copies to the VMU.

Compared with the US release's VMU art (Jet Grind Radio v1.005), 11 of its 12
game screens and all 721 font glyphs are here byte for byte. What differs is
Japanese: the logo and the viewer's text.

## The game's screens

Twelve screens sit back to back in `1ST_READ.BIN` at `0x8C1C0330` (it loads at
`0x8C010000`). Each is 192 bytes packed 1 bit per pixel (1 = lit), turned 180°
the way the VMU's LCD takes it, as in Crazy Taxi 2. Two tables follow them:

| Table        | What it holds                                                         | Read by      |
| ------------ | --------------------------------------------------------------------- | ------------ |
| `0x8C1C0C30` | screens by number: logo, OK, NG, Now Saving, Now Loading, logo again  | `0x8C0AA990` |
| `0x8C1C0C80` | animations, each a null-terminated list of screens: the radio, then 1 | `0x8C0AA9D4` |

`0x8C0AA990` shows one screen; its 31 callers pass numbers 0 to 4, so every
screen in the first table is shown. The logo is the katakana ジェットセットラジオ;
the US disc has the Jet Grind Radio logo in its place. The archive's older
"Title screen" entry, a Latin JET SET RADIO logo, isn't on this disc in any
packing.

The radio turns by playing poses 1–7 and back (1, 2 … 7, 6 … 2), twelve steps
on a loop. `0x8C0AA9D4` steps the list when the VMU task's counter divided by
a period leaves nothing (the division is `0x8C013DE0`), and its only caller,
`0x8C017E72`, asks for a period of 6. That's 100 ms a step if the task runs
every frame at 60 Hz. The rate is assumed, not measured; a capture would
settle it.

The second animation in the table runs through the first table (logo, OK, NG,
Now Saving, Now Loading, logo) but nothing plays it. It's those same screens in
a row, not art of its own, so the archive doesn't have it.

## The graffiti viewer

`/JETRADIO/SYSOPTION.AFS` holds three members. The first is a VMS file whose
header names it `JET_VM_APLI`, described in Shift-JIS as ジェット VM実行ファイル
("Jet VM program"). It lets the VMU show the graffiti downloaded from the Jet
Set Radio channel online. Its addresses below are offsets into that file, which
runs from 0 in the VMU's flash. The second member (196,520 bytes) and the third
(a PVR texture) weren't looked into.

It draws four ways:

- `0x0BD3`: a bitmap, a byte for its width in bytes and one for its height,
  then the rows. The channel screen (48×32 at `0x1A73`), the © SEGA text and
  the SEGA logo (48×20, at `0x33DA` and `0x3454`).
- `0x0C38`: a sprite up to 8 pixels wide: width, height, a byte a row. It
  replaces the pixels in its box. The radio is three of them (`0x19A3`,
  `0x19BD`, `0x19D7`).
- `0x1C94`: a string, an x and y, then two bytes a character: a font and a
  glyph. `FE FE` starts a new line 8 pixels down, `FD` adds a 4-pixel space,
  and `FF FF` ends it. The strings are at `0x32CA`–`0x34FF`.
- `0x1DD5`: a line across the screen.

Its fonts, kept as sprite sheets:

| Font          | Address  | Glyphs | Size | Notes                                                                     |
| ------------- | -------- | ------ | ---- | ------------------------------------------------------------------------- |
| Title (`E0`)  | `0x19F1` | 13     | 8×8  | JET SET RADIO and Press A+B                                               |
| Narrow (`01`) | `0x21BB` | 151    | ≤8×8 | ASCII from `0x20`, then half-width kana; each character advances 4 pixels |
| Wide (`02`)   | `0x27A1` | 123    | ≤8×8 | symbols, digits, Latin                                                    |
| Kana (`03`)   | `0x2C6F` | 161    | ≤8×8 | katakana, then hiragana                                                   |
| Small         | `0x0DEE` | 256    | 5×7  | a full character set, 7 bytes a glyph, no header; read at `0x0DA4`        |
| Hex digits    | `0x0C98` | 17     | 3×5  | 0–9, A–F and a blank, 5 bytes a glyph                                     |

Glyphs in the first four are 10 bytes: width, height, 8 rows. The narrow,
wide and kana sheets have 16 glyphs a row in 8×8 cells; the small font and
hex digits leave a pixel between cells.

### The screens

The archive's viewer screens are rebuilt by drawing what the code draws, at
the places it gives, rather than captured:

- **SEGA** and **copyright** (`0x14EE`): when the viewer starts, the SEGA
  logo at (0, 4) for 32 ticks, then the © text at (0, 6) for 32 ticks, each
  shown once before the title. Each 48×20 bitmap fills its screen alone, so
  neither is kept as a sprite.
- **Title** (`0x152E`): the radio at x = 12, 20, 28 with JET SET RADIO under
  it (`0x3382`) for 16 ticks, then Press A+B (`0x3372`) for 16, until A or B
  is pressed. A third string, JET SET RADIO at the top (`0x3392`), is never
  drawn.
- **Downloaded graffiti** (`0x1574`): the channel screen, its Press A row
  blinking: 16 ticks hidden (`0x09ED` clears 48×8 at y = 24), 16 shown.
- **Size menu** (`0x15E5`): グラフィティ over a line, then スモール, ラージ and
  ×・ラージ, with the cursor (narrow font glyph `0x2A`) at the first.
- **No graffiti** (`0x1690`): when nothing was downloaded, the choices give way
  to "DLしてきた / グラフィティなし / B モドル" with a line above the last row.

Screens that show a downloaded graffiti's title, comment or e-mail address
(タイトル, コメント, メールアドレス) draw data that isn't on the disc, so they
aren't in the archive.

A tick is one wake-up from the VMU's base timer (interrupt 1, counted in
`0x01E` and waited for by `0x0578`). The program never sets the timer's rate
itself, so the ticks aren't converted to milliseconds, and the animations play
at the site's default.

The radio, the SEGA screens and the fonts are byte for byte the same on the US
disc, so they have no region; the screens with Japanese text are `JP`.
