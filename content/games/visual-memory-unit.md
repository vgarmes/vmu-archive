# Visual Memory Unit

Scripts: `tools/disc-extraction/bios/`.

Source: the US VMU BIOS v1.05 (1999/10/26), through its commented disassembly,
[gyrovorbis/vmu-bios-disassembly](https://github.com/gyrovorbis/vmu-bios-disassembly).
It's the firmware in the VMU's own CPU (a Sanyo LC86K87): everything the VMU
shows without a game, while it isn't plugged into a controller. The Japanese
BIOS v1.004 (1998/09/30) is a different program with art of its own; it's
described [below](#the-japanese-bios), and its pieces are marked Japan.

## What's in the ROM

| Address | Label             | Holds                                          | Archive entry                  |
| ------- | ----------------- | ---------------------------------------------- | ------------------------------ |
| `$0473` | `FontGlyphs8x8`   | 42 glyphs, 8x8: 0–9, `:`, two arrows, `/`, A–Z | Big font (sprite)              |
| `$05C7` | `Str_VmuBanner`   | The main menu's text                           | Main menu                      |
| `$18CF` | `AnimSprites`     | Clock animals, 8x8: dog, fish, bird, two each  | Clock dog, fish, bird (sprite) |
| `$18FF` | `AnimSpriteBlank` | A blank 8x8 sprite                             | —                              |
| `$1907` | `AnimSequences`   | Each animal's path across the screen           | —                              |
| `$E800` | `FontAscii6x8`    | 256 characters, 6x8                            | Small font (sprite)            |

No whole screen is stored: the BIOS builds every screen from these fonts and
sprites. The four icons along the LCD's bottom edge (file, game, clock, flash
access) aren't bitmaps; they're segments of the glass, each switched by one bit,
so there's nothing to keep.

## Main menu

`MainMenu` (`$02EF`) clears the screen and draws `Str_VmuBanner` with the small
font in its 8x4 grid of 6x8 cells: the bold SEGA logo (characters `$17`–`$1A`),
then "Visual", "Memory" and "Unit" on their own lines. It's shown every time the
VMU comes back to its menu, while MODE cycles the blinking icon between file,
game and clock. It's the one piece here that fills the screen, so it's the
archive's screen; drawn from the font exactly as `DrawString` does.

## Clock animation

In clock mode the lower half of the screen runs an animation, chosen with Up and
Down: a dog, a fish or a bird (`ClockAnimationStep`, `$1805`, once a second).
The animal steps right one 8-pixel column at a time through the six positions in
`AnimSequences`, alternating its two frames, and each step leaves the last
sprite where it was, so a trail of six builds up. The next pass walks the blank
sprite through the same positions and wipes them one by one.

- The dog runs diagonally down the half, a line a step.
- The fish bobs between two heights. Its two frames are the same bytes, so it
  has one pose, kept once.
- The bird climbs from the bottom to the top: it takes off.

`vmubios.py` replays this in its contact sheet. The sprites are kept on their
own; they're drawn on the clock screen, which isn't in the archive.

## Fonts

The big font draws the time (HH:MM) and the date fields, and spells the month
names: it has no lower case, so its letters are found with ASCII minus `$31`. The
`/` is stored three times.

The small font draws all other text. Besides ASCII it has the half-width
katakana, the SEGA logo, the A and B button icons (`$1A`, `$1B`), arrows, card
suits, a "No." sign and eight frames of a spinner (`$F0`–`$F7`, which the
disassembly ties to the connector).

Both are kept the archive's way for fonts: the characters one under the next,
in character order, 8 rows each. The big font is stored that way, 8 bytes a
character, so its sprite is `FontGlyphs8x8`'s 336 bytes as they are. The small
font is stored in planes instead: plane n holds row n of all 256 characters, and
only the top 6 bits of each byte are used. `vmubios.py` restacks it a character
at a time, 6 pixels wide, after checking that the low 2 bits are 0 in every
byte and that the stack rebuilds the 2048 bytes of planes.

## The Japanese BIOS

Source: the Japanese VMU BIOS v1.004 (1998/09/30), ROM md5
`1c75e99bdc6d88a855da1ce212c2b38a`, read with `vmubios_jp.py`. There's no
disassembly of it, so it was read by drawing the whole ROM as 1-bit images and
comparing it with the US one. Its code ends at `$3FF7` (the US's runs on into
`$7FFF`). `$E000`–`$EFFF`, the small font included, is the US ROM's byte for
byte; the rest is its own.

| Address | Holds                                                      | Archive entry                           |
| ------- | ---------------------------------------------------------- | --------------------------------------- |
| `$0473` | Big font: 48 glyphs, 8x8, three sets of 16                 | Big font (sprite, Japan)                |
| `$05F7` | The main menu's text                                       | Main menu (Japan)                       |
| `$0F1A` | Clock animals, 8x8: cat, fish, helicopter, two frames each | Clock cat paw print, helicopter (Japan) |
| `$0F4A` | Each animal's path across the screen                       | —                                       |
| `$0F5F` | The clock's menu text and the animals' names, in katakana  | —                                       |

There is still no bitmap of the mode icons: the Japanese VMU has the same
segments on its glass.

**Big font.** It has no letters. Each of its three sets is 0–9, `:`, the two
arrows, then 年, 月 and 日, so the date is written with kanji where the US
spells the month. The sets are thin, bold and a thin one with a slashed zero; the bold
set's digits, colon and arrows are the US big font's. The code loads only
`$0473` as the table's address (at `$1B7E`), so the three sets are one table,
48 glyphs, kept as one sprite. The clock's text has モジ センタク, "choose
characters", next to アニメ センタク, so the set is likely the owner's pick for
the clock's digits; the code that picks it wasn't traced.

**Main menu.** Drawn at the top left by the BIOS's string routine (`$1C93`,
called from `$02FD`) with the small font, as the US does: the SEGA logo, then
"Visual" and "Memory", with no "Unit". Their V and M are the font's characters
`$15` and `$16`, bold capitals the US menu doesn't use (it has a plain V and M).

**Clock animals.** The clock's menu names them ヘリコプター, ネコ and サカナ:
helicopter, cat and fish; the table holds them cat, fish, helicopter, each
with its two frames the same bytes, so none of them changes pose. The paths use the US
format (a count, then screen-memory offsets):

- The cat is its paw print: it steps right a column at a time, down and up
  8 dots in turn, leaving a trail of footprints.
- The fish is the US's fish, byte for byte, bobbing 2 dots as in the US.
- The helicopter climbs 2 dots a step, drops back down and climbs again.

There's no blank sprite after the animals as in the US ROM; how the trail is
wiped wasn't traced.
