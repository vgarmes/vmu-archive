# Visual Memory Unit

Scripts: `tools/disc-extraction/bios/`.

Source: the US VMU BIOS v1.05 (1999/10/26), through its commented disassembly,
[gyrovorbis/vmu-bios-disassembly](https://github.com/gyrovorbis/vmu-bios-disassembly).
It's the firmware in the VMU's own CPU (a Sanyo LC86K87): everything the VMU
shows without a game, while it isn't plugged into a controller. The Japanese
BIOS wasn't checked, so everything here is marked US.

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
disassembly ties to the connector). Both are kept as sheets in character order, the small one 32
characters a row.
