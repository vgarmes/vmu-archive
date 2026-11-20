# Capcom vs. SNK: Millennium Fight 2000

Scripts: `tools/disc-extraction/cvs/`.

Dump: Redump `Capcom vs. SNK - Millennium Fight 2000 (Japan) (Rev A)` (`.cue`
and three `.bin` tracks). Neither screen has Japanese text, so they get no
region.

## What's on the disc

No file holds the VMU screens. `SPR_VMU.BIN` and `SPR_VMJ.BIN` sound like VMU
art but are compressed colour data (they start `_E`), and `DPETC/VMS.DPS`
belongs to the bundled Dream Passport browser, as in Marvel vs. Capcom 2. Two
screens sit back to back in `1ST_READ.BIN`, which runs from `0x8C010000`, just
before the save icons, stored as shown (1 bit per dot, high bit first, 1 =
lit).

| Screen | Address      | Archive entry |
| ------ | ------------ | ------------- |
| Logo   | `0x8C1B990C` | Title screen  |
| ACCESS | `0x8C1B99CC` | Access        |

The VMU code is Marvel vs. Capcom 2's. Every caller loads a screen's address
into `r4` and calls `0x8C067018`, which spreads its bits into a byte buffer at
`0x8C1B9A8C` (8 for a 1 bit, 0 for a 0 bit); `0x8C06705E` then hands the
buffer to the library's LCD write (`0x8C1FD888`) for one VMU, picked from the
table of slot addresses at `0x8C1B98EC` (1, 2 for port A's two slots, 7, 8 for
port B's, and so on), with a flag of 0 or 3 from a query of the device. Nothing
inverts or mirrors, so the VMU shows both screens as stored. The logo is loaded
from six places and ACCESS from three, all in the memory card code
(`0x8C0670BA`–`0x8C06956A`); what picks one wasn't traced, the names say when
they show. Nothing animates.

The buffer isn't empty on the disc. Its 1,536 bytes hold the letters "VS4" as
the copy routine would leave them, the same leftover Marvel vs. Capcom 2's
buffer holds (VS4 is that game's VS.COM program). The game fills the buffer
before every send, so it's never shown, and it isn't kept.

## Save icons

The save table holds two pointer tables of 16 entries, one per save type:
palettes at `0x8C1BAD4C` and frames at `0x8C1BAD8C`. They point at six
distinct icons:

| Types | Palette      | Frame        |
| ----- | ------------ | ------------ |
| 0     | `0x8C1BA90C` | `0x8C1BA92C` |
| 1, 2  | `0x8C1BA2AC` | `0x8C1BA2CC` |
| 3     | `0x8C1BAB2C` | `0x8C1BAB4C` |
| 4     | `0x8C1BA08C` | `0x8C1BA0AC` |
| 5–14  | `0x8C1BA4CC` | `0x8C1BA4EC` |
| 15    | `0x8C1BA6EC` | `0x8C1BA70C` |

The program names the saves `CAPVSSNK_SYS`, `_UPL`, `_DNL` and `_RD0` to
`_RD9` on the memory card (from `0x8C181578`), with VMU names and
descriptions `CVS.S_SYSTEM`, `CVS.S_REPLAY`, `CVS.S_UPLOAD` and
`CVS.S_DOWNLOAD` (from `0x8C1B9708`). The ten types sharing one icon are
probably the ten replays; the rest weren't matched to their types.

- **Confirmed.** The System file icon already in the archive, read from a
  dumped save, is the game's own: its frame is at `0x8C1BA2CC`.
- **Not the game's.** The memory card icon (`ICONDATA_VMS`, `CAPVSSNK`) isn't
  on the disc: neither its colour frame, its palette nor its one-colour VMU
  icon turns up in any track. Its picture is the System file icon's pixel for
  pixel, with the same colours in another order, and the program doesn't hold
  the name `ICONDATA_VMS` at all. A tool made it from the System file icon.
- The other five icons have no dumped save in the archive and aren't imported
  yet.
