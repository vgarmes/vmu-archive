# Power Stone

Scripts: `tools/disc-extraction/power-stone/` (release `ps1`), shared with
[Power Stone 2](power-stone-2.md).

Dump: `Power Stone v1.020 (1999)(Capcom)(JP)[!][1MB1]` (`.gdi`).

The name and logo are the same in every release, so nothing from this disc gets
a region.

## What's on the disc

No file holds VMU art. The game keeps two screens in `1ST_READ.BIN`, which loads
at `0x0C010000` (the `0x0C` alias of main RAM, like Moero! Justice Gakuen), so
`common/find_code.py` can't see their references.

They were found by searching for the archive's title screen, which matched only
with its bits inverted. Each screen has a routine that turns it into a byte
buffer (8 = lit) for the VMU, and the routine sets the polarity.

| Screen | Address      | Routine      | Stored   | Archive entry                                |
| ------ | ------------ | ------------ | -------- | -------------------------------------------- |
| Title  | `0x0C17C198` | `0x0C020174` | inverted | Title screen (already in the archive, exact) |
| ACCESS | `0x0C17C258` | `0x0C0201BC` | as shown | Access                                       |

Both routines have many callers in the save and load code, so every screen is
shown. Nothing animates.

The archive's Power Stone title came from a screenshot, through an older version
of the importer that read a screenshot's majority colour as unlit. It got this
one right: the disc stores the title inverted, and the game inverts it again
before sending it, so the entry matches the disc exactly.
