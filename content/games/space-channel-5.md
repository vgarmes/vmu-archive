# Space Channel 5

Scripts: `tools/disc-extraction/space-channel-5/`.

Dump: Redump `Space Channel 5 (Japan)` (`.cue` and five `.bin` tracks;
HDR-0029 V1.001, 1999-11-28). None of the screens has Japanese text and
nothing shows the other releases lack them, so they have no region.

## What's on the disc

No file holds VMU art. It's all in `1ST_READ.BIN`, which runs from
`0x8C010000` and carries its own copy of Sega's sample LCD module,
`vmslcd.c` (named by its error message, "This size is not supported in
vmslcd.c."). The round files (`ROUND1.BIN` to `ROUND4.BIN`, run from
`0x8C270000`) don't touch the VMU.

The module keeps 15 images, listed at `0x8C03C090` as pairs of a rectangle
(x, y, width, height as four 32-bit numbers) and its bitmap, which follows the
rectangle: 1 bit a dot, high bit leftmost, upright. Its blitters
(`0x8C030530`, `0x8C03065A`) copy an image to its place on a blank 48x32
screen, a byte a dot, and the sender (`0x8C0307FE`) writes the screen to the
first VMU it finds. The images sit back to back from `0x8C03B4A8` up to the
table, and every one of them is in it.

| Entry | Rectangle     | Shown                                                                     | Archive entry          |
| ----- | ------------- | ------------------------------------------------------------------------- | ---------------------- |
| 0     | 0, 6, 48 × 20 | the resting screen: whenever no other is set                              | Channel 5 logo         |
| 1     | full screen   | `show(1)` at `0x8C010940`                                                 | Now loading            |
| 2     | full screen   | `show(2)` at `0x8C010A74`, in the save code                               | Now saving             |
| 3     | full screen   | `show(3)` at `0x8C02D9F8`, in the routine that loads the staff roll's art | Sibuya                 |
| 4–14  | full screen   | portraits 0–10, one for each character number (see below)                 | Ulala, 10 unidentified |

The LCD setup (`0x8C0304CC`) draws entry 0 into the screen the sender falls
back to when no other is set, so the logo is the VMU's resting screen;
`show(0)` (`0x8C030942`) goes back to it. `show(n)` draws entry n.

The portraits come from `0x8C030928`, which shows entry 4 + k for character
k. A scene object (`0x8C021E74`) shows its character's portrait in one mode
and portrait 0, Ulala, in another, and goes back to the logo when done. Which
scenes set which character wasn't traced, so only Ulala is named; the other
ten are `Unidentified portrait`, in the game's order (entries 5–14).

The module also has a text ticker (`0x8C030984`) that scrolls a Shift-JIS
string across the screen, but nothing in the program or the round files ever
starts it.

## Save icon

The save header is built around `0x8C010786`: palette at `0x8C03ADD8`, three
frames at `0x8C03ADF8`, animation speed 4. The game names its saves
`SPACECH5_001` to `SPACECH5_008`, and has a `SPACECH5_DBG`; all use this one
icon.

- **Confirmed.** The save icon already in the archive, read from a dumped save,
  is the game's own: its palette and all three frames match the program's byte
  for byte. The ten dumped saves in that collection, Japanese and American,
  carry the same icon.
