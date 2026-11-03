# Power Stone 2

Scripts: `tools/disc-extraction/power-stone/` (release `ps2`), shared with
[Power Stone](power-stone.md).

Dump: `Power Stone 2 v2.000 (2000)(Capcom)(JP)[!]` (`.gdi`).

The name and logo are the same in every release, so nothing from this disc gets
a region.

## What's on the disc

No file holds VMU art. Like Power Stone, the game keeps two screens in
`1ST_READ.BIN`, which loads at `0x0C010000` (the `0x0C` alias of main RAM), so
`common/find_code.py` can't see their references.

They were found by searching for the expansion code found in Power Stone: each
screen has a routine that turns it into a byte buffer (8 = lit) for the VMU,
and the routine sets the polarity.

| Screen | Address      | Routine      | Stored   | Archive entry |
| ------ | ------------ | ------------ | -------- | ------------- |
| Title  | `0x0C210084` | `0x0C03A670` | as shown | Title screen  |
| ACCESS | `0x0C210144` | `0x0C03A6B6` | as shown | Access        |

Both routines have many callers in the save and load code, so every screen is
shown. Nothing animates.
