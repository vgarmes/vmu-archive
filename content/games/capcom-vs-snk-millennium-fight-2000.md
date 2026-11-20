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

The header builder, `0x8C067D58`, takes a save type (0–15). It zeroes its
record, copies the VMU name and description in a switch over types 0–14
(jump table `0x8C067D98`), then takes the palette from the 16 pointers at
`0x8C1BAD4C` and the frame from those at `0x8C1BAD8C`, one frame at animation
speed 5. Each icon is drawn with what it's for, which names the types the
switch leaves blank. The memory card names are at `0x8C181578` on, matched to
the types by what they say.

| Types | Memory card name         | VMU name           | Palette      | Frame        | Archive entry                       |
| ----- | ------------------------ | ------------------ | ------------ | ------------ | ----------------------------------- |
| 0     | `CAPVSSNK_UPL`           | `CVS.S_UPLOAD`     | `0x8C1BA90C` | `0x8C1BA92C` | UPLOAD file (from the disc)         |
| 1, 2  | `CAPVSSNK_SYS`           | `CVS.S_SYSTEM`     | `0x8C1BA2AC` | `0x8C1BA2CC` | System file (confirmed)             |
| 3     | `CAPVSSNK_DNL`           | (`CVS.S_DOWNLOAD`) | `0x8C1BAB2C` | `0x8C1BAB4C` | DOWNLOAD file (from the disc)       |
| 4     | `CAP_NET_.NET`           | `CAP-NET_NETﾌｧｲﾙ`  | `0x8C1BA08C` | `0x8C1BA0AC` | Capcom network file (from the disc) |
| 5–14  | `CAPVSSNK_RD0` to `_RD9` | `CVS.S_REPLAY`     | `0x8C1BA4CC` | `0x8C1BA4EC` | Replay file (from the disc)         |
| 15    | none                     | none               | `0x8C1BA6EC` | `0x8C1BA70C` | Color edit file (from the disc)     |

- **Confirmed.** The System file icon already in the archive, read from a
  dumped save, is the game's own: the rebuilt header's palette and frame
  match it.
- **From the disc.** `saves.py` rebuilds each other header as the builder
  does and they're imported with the disc as their source, kept as `ntsc-j`,
  as their names are. The colour edit file has no text and gets no region.
- **DOWNLOAD.** The switch sends type 3 past the names, and nothing loads the
  DOWNLOAD name and description that sit in place after UPLOAD's
  (`0x8C1B9864`). Its icon is UPLOAD's VMU under a blue arrow pointing down,
  and the memory card name `CAPVSSNK_DNL` is in the program, so the entry
  carries those strings; what writes this file's header wasn't traced.
- **COLOR.** Type 15 is past the switch too, and the program holds no name for
  it. Its icon says COLOR, and the game has a COLOR EDIT MODE. What writes it
  wasn't traced.
- The CAP-NET icon isn't Marvel vs. Capcom 2's: same purpose, different art.
- **Not the game's.** The memory card icon (`ICONDATA_VMS`, `CAPVSSNK`) isn't
  on the disc: neither its colour frame, its palette nor its one-colour VMU
  icon turns up in any track. Its picture is the System file icon's pixel for
  pixel, with the same colours in another order, and the program doesn't hold
  the name `ICONDATA_VMS` at all. A tool made it from the System file icon.
