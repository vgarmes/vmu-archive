# Crazy Taxi 2

Scripts: `tools/disc-extraction/crazytaxi2/`.

Dump: `Crazy Taxi 2 v1.004 (2001)(Sega)(US)[!]` (`.gdi`). The name and logo
are the same in every release, so nothing from this disc gets a region.

## What's on the disc

No file holds VMU art, and the disc doesn't contain Crazy Taxi's title screen in
any packing. The screens are in `1ST_READ.BIN`, which loads at `0x0C010000` (the
`0x0C` alias of main RAM), so `common/find_code.py` can't see their references.

They were found by following the code back from Kamui's LCD library (`pdLcd Ver
1.04` is linked in). `0x0C14B2C6` sends 192 bytes to one VMU's screen, and its
only caller is `0x0C058DE0`, which sends that VMU's slot of the game's screen
buffer (`0x0C2B1624`, 1536 bytes for each of 4 ports × 2 slots). Two routines
draw into that buffer, and both draw a screen through `0x0C058E82`:

| Screens        | Address               | Drawn by     | Archive entry |
| -------------- | --------------------- | ------------ | ------------- |
| Logo, 3 frames | table at `0x0C130644` | `0x0C058C18` | Title screen  |
| Now Loading    | `0x0C10C574`          | `0x0C058CCA` | Now Loading   |
| Now Saving     | `0x0C10C638`          | `0x0C058CCA` | Now Saving    |

Each screen is a 48×32 sprite: a big-endian width and height, then 192 bytes
packed 1 bit per pixel (1 = lit), turned 180°, the way the VMU's LCD takes it.

The drawing routine was written for 1 byte per pixel: it copies 48 bytes a row
into a buffer 48 bytes wide. Every screen is drawn at (0, 0), so the first 192
bytes it sends are the packed screen anyway. An unused routine at `0x0C058F46`
fills every VMU's buffer with `0x80`, which would show vertical lines 8 pixels
apart. Nothing calls it, and it isn't art, so it isn't in the archive.

## The logo

Flames above the Crazy Taxi 2 logo, with a striped line along the bottom that
moves 2 pixels a frame. It's the same stripe as the border of Crazy Taxi's
title screen. `0x0C058C18` runs once per main-loop frame, from the game's main
loop at `0x0C01B100`, and updates one VMU slot per call. After all 8 slots it
adds 1 to a counter that wraps at 640. The frame shown is (counter ÷ 2) mod 3,
so each frame lasts 16 loop frames: 267 ms if the loop runs at 60 Hz, the same
speed as the archive's Crazy Taxi title screen. That rate is assumed, not
measured; a capture would settle it. When the counter wraps, the third frame is
skipped once, about every 85 seconds.

The routine skips any slot without a screen, and stops while the game is
loading or saving. `0x0C058CCA` then clears the screen and shows Now Loading
or Now Saving. Its only callers are the save and load code (`0x0C036A9E`,
`0x0C036D6C`, `0x0C037402`, `0x0C037B72`). Every screen is shown, so none is
marked unused.
