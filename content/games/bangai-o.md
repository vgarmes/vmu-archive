# Bakuretsu Muteki Bangaioh

Scripts: `tools/disc-extraction/bangaioh/`.

Dump: `Bakuretsu Muteki Bangaioh v1.003 (1999)(ESP)(JP)[!]` (`.gdi`). The archive
files these under `Bangai-O`, with region `ntsc-j` on what came from this disc.

## What's on the disc

No file on the disc holds VMU art. The 24 screens sit in `1ST_READ.BIN` at
`0x8C05D460`, 192 bytes each, packed 1 bit per pixel (high bit first) and rotated
180°, the way the VMU's LCD takes them. They were found by searching every file for
the archive's Bangai-O "Robot" capture in every packing and orientation.

Seven animation scripts follow at `0x8C05E6FC` (format in `vmu.py`). The VMU
routine at `0x8C05125C` ticks them at 60 Hz. One caller (`0x8C014C16`) starts
script 3 or 5 in game states 17, 18, 23, 24, 29 and 30, picking by the pilot flag
at `0x8C4C8E54`, and script 1 otherwise. Nothing starts 0, 2, 4 or 6, so those
are marked `unused`.

| Script | Screens | Hold (ms) | Archive entry |
| --- | --- | --- | --- |
| 0 | 0 | still | Treasure logo (unused) |
| 1 | 1 | still | Title screen (JP logo) |
| 2 | 2, 3, 4, 5, 2, 5 | 133 each | Mode: Riki (unused) |
| 3 | 2, 6, 7, 8, 2, 8 | 133 each | Mode: Riki |
| 4 | 9, 10, 11, 12, 9, 12 | 133 each | Mode: Mami (unused) |
| 5 | 9, 13, 14, 15, 9, 15 | 133 each | Mode: Mami |
| 6 | 16–23 | 67 each | Continue? (unused) |

The archive's earlier "Robot" capture is script 3's loop from the US release: the
same frames and the same 133 ms, but with the header (rows 2–6) redrawn, so it
isn't on this disc. The US title screen isn't either.
