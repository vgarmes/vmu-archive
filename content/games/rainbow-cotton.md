# Rainbow Cotton

Scripts: `tools/disc-extraction/rainbow-cotton/`.

Dump: Redump `Rainbow Cotton (Japan)` (`.cue` and three `.bin` tracks;
T-9901M V1.009, 1999-12-01). The game was only released in Japan, so its pieces
are `ntsc-j`.

## What's on the disc

No file holds VMU art, and `1ST_READ.BIN` has none either: it's a small loader
for the game's overlays, which all run from `0x8C200000`. `TITLE.BIN` runs the
title and menus; `GAME.BIN`, `BO01.BIN` and `LAST.BIN` run the stages. Each
links Sega's `pdLcd` library (version 1.04) and carries its own copy of the VMU
code and art at its own addresses. The 16 screens and the animation table are
byte for byte the same in all four. Addresses below are `TITLE.BIN`'s.

The screens are 192 bytes each from `0x8C2122E4`, packed 1 bit a dot, high bit
leftmost, upright. The game's send (`0x8C20B27C`) unpacks one into a byte a dot
(8 lit) at `0x8C4E4D44` and hands it to `pdLcd`'s write (`0x8C21451C`) for the
first controller's VMU.

## Animations

A small player (`0x8C20B1D0`) steps one animation at a time. An animation is a
list of a screen pointer and a hold in ticks; a hold of -2 goes back to its
first step and -1 switches to the animation queued next (`0x8C20B24A`). The
eleven animations are listed at `0x8C2130B4`. The player is ticked once a pass
of the game loop, just before the frame wait, so a tick is taken as a 60 Hz
frame.

| Animation | Screens                   | Hold (ticks)              | Started from | Archive entry |
| --------- | ------------------------- | ------------------------- | ------------ | ------------- |
| 0         | 7, 8                      | 30 each, loops            | the title    | Title logo    |
| 1         | 9                         | held                      | the stages   | Now loading   |
| 2         | 0, 1, 2 (three times)     | 60, 2, 2, 60, 2, 2, 20, … | the stages   | Blinking      |
| 3         | 3                         | 30, then the next one     | the stages   | Seeing stars  |
| 4         | 4, 5, 6                   | 4 each, loops             | the stages   | Dizzy         |
| 5–10      | 10–15 (mouths), ending 15 | 2–8, then the next one    | the stages   | Talking       |

The title overlay only starts the logo; the stage overlays start all the rest.
What in play triggers each one wasn't traced, so the entries are named for what
they show. Every screen and every animation is used.

## Save icon

`TITLE.BIN` builds the save header (`R_COTTON.SCO`) at `0x8C20B4F0`: palette at
`0x8C213CF0`, two frames at `0x8C213D10`, animation speed 10, named
`Rainbow COTTON` and レインボー コットン. It is the game's only save.

- **Confirmed.** The save icon already in the archive, read from a dumped save,
  is the game's own: its palette and both frames match the program's byte for
  byte.
