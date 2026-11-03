# Soul Calibur

Scripts: `tools/disc-extraction/soulcalibur/`.

Dump: `Soul Calibur v1.000 (1999)(Namco)(US)[!][1S]` (`.gdi`). The chibis are
the same in every release, so nothing from this disc gets a region.

**Partly imported.** The 19 character animations are in the archive, without
timing yet (see [Waiting](#waiting)). The title screen already in the archive
came from a screenshot and hasn't been found on the disc.

## What's on the disc

No VMU art is stored uncompressed: searches for the archive's title screen and
the chibis as packed bits, one byte per dot, column or page order, flipped,
mirrored and inverted, over every file, found nothing. Generic LZSS and PRS
didn't find them either.

The game has its own decompressor at `0x8C0EE76C` in `1ST_READ.BIN`, called from
about 30 places. A flag byte is read low bit first: 1 copies a byte, 0 is a
two-byte reference, big-endian, with the length (minus 1) in the top 5 bits and
the distance back (minus 1) in the low 11. A flag of 1 means read the next flag
byte, 0 ends the data, and `0xFF` copies seven bytes. `vmu.py` has it as `lz()`.

The `.DAT` files are `olnk` archives (`u32` count, `"olnk"`, `u32` header size,
`u32` total, then count × `{u32 offset, u32 size}` from the end of the header).
Their members are mostly tables of their own: `u32` count, then count `u32`
offsets from the member's start.

`HUMAN.DAT` holds one member per character and costume (member index ÷ 10 is
the character). Entry 6 of each is its VMU set: compressed, it unpacks to 7684
bytes, a `u32` 48 (the width), then 5 frames of 48×32 at one byte per dot.

| Value | Meaning                             |
| ----- | ----------------------------------- |
| 15    | lit                                 |
| 0     | unlit, inside the figure            |
| 128   | unlit, background around the figure |

The two unlit values suggest the game draws the figure over something; on the
VMU both show unlit. A character's costume members repeat the same set, so the
45 sets hold 19 different characters; `vmu.py` keeps the first of each.

All 95 frames match, in order, the 19 × 5 frames of an independent decode.

## Waiting

1. **Timing.** The entries carry no frame delay, so the site plays them at its
   default. Capture one character in Flycast for the order and speed the game
   uses; the frame order here is the order on the disc.
2. **Title screen.** Not among the 857 members that decompress cleanly, at least
   not matching the screenshot-made entry exactly.
