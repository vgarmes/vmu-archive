# Super Puzzle Fighter II X for Matching Service

Scripts: `tools/disc-extraction/spf2x/`.

Dump: `Super Puzzle Fighter II X for Matching Service (Japan)` (Redump, `.cue`;
T-1250M V1.001, 2001-04-24). The game came out in Japan alone, so everything
from it is `ntsc-j`.

## What's on the disc

No file holds VMU art. `VM00.BIN` and `VM00_TBL.BIN` sound like it but are
the TV screen's sprite layouts (positions up to 320 dots wide), and
`DPETC/VMS.DPS` belongs to the bundled Dream Passport browser, as in Street
Fighter III 3rd Strike and Marvel vs. Capcom 2. The screens are in
`1ST_READ.BIN`, which links Sega's `pdLcd` library and runs from
`0x8C010000`. With no screen in the archive to search for, they were found by
drawing the data before the save-file names (`SUPAZULU.SYS`) as 48-pixel-wide
1-bit rows, as for Street Fighter III. Four screens sit back to back, stored
in the archive's own encoding (1 bit per pixel, high bit first, 1 = lit):

| Screen | Address      | Shown | Archive entry  |
| ------ | ------------ | ----- | -------------- |
| Title  | `0x8C1747FC` | yes   | Title screen   |
| ACCESS | `0x8C1748BC` | yes   | Access         |
| OK!    | `0x8C17497C` | no    | OK (unused)    |
| ERROR! | `0x8C174A3C` | no    | Error (unused) |

The VMU code is Marvel vs. Capcom 2's, laid out as in [Vampire
Chronicle](vampire-chronicle-for-matching-service.md), the other Matching
Service game. Each send loads a screen's address into `r4` and calls
`0x8C0CF2B2`, which spreads its bits into a byte buffer at `0x8C1741FC` (8 for
a 1 bit, 0 for a 0 bit), then `0x8C0CF31C` sends the buffer through the
library's LCD write. There are seven sends, all in the memory card code
(`0x8C0CEA98`–`0x8C0CF1EC`): ACCESS when a save or load starts (`0x8C0CEA94`,
`0x8C0CEDD2`), and the logo from the other five. Nothing inverts on the way,
so the screens show as stored: the logo is mostly lit dots, with a line of
text along the bottom too small to read. Nothing animates.

**OK! and ERROR! are never shown.** They follow ACCESS in the same block, but
nothing loads them, by address or by an offset from ACCESS, as in Vampire
Chronicle. They're kept, tagged `unused`.

**The buffer isn't empty on the disc.** Its 1,536 bytes hold a smiling face
between brackets, drawn in single-dot lines, as Vampire Chronicle's does. Every
send fills the buffer first, so the VMU never shows it, and it isn't kept.
`vmu.py` writes it out as `lcd/buffer.png`.

## Save icons

The header builder (`0x8C0CF362`) takes a file type: the VMU name and
description from `0x8C173D24` on, the palette from the pointers at
`0x8C1741EC` and the one frame from `0x8C1741F4`, at animation speed 5. The
memory card names are at `0x8C174B1C`. `vmu.py` rebuilds each header as the
game does, and they're imported with the disc as their source.

| Type | Memory card name | VMU name / description                          | Palette      | Frame        | Archive entry                    |
| ---- | ---------------- | ----------------------------------------------- | ------------ | ------------ | -------------------------------- |
| 0    | `SUPAZULU.SYS`   | ｽﾊﾟｽﾞﾙ\_\_ｾｰﾌﾞﾃﾞｰﾀ / スパズル セーブデータ      | `0x8C173DAC` | `0x8C173DEC` | Save file                        |
| 1    | `CAP_NET_.NET`   | CAP-NET_NETﾌｧｲﾙ / カプコン ネットワークファイル | `0x8C173DCC` | `0x8C173FEC` | Marvel vs. Capcom 2's, identical |

The Capcom network file's icon is byte for byte the one Marvel vs. Capcom 2
writes, so it's kept once, under that game. The name table also holds
`SPF2X___.DBG`, a debug file the header builder has no case for.
