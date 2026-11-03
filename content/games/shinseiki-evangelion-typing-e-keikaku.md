# Shinseiki Evangelion: Typing E-Keikaku

Scripts: `tools/disc-extraction/eva-typing/`.

Dump: `Shinseiki Evangelion - Typing E Keikaku v1.001 (2001)(Gainax)(JP)[!][req. keyboard]`
(`.gdi`). The game was only released in Japan and its logo is Japanese, so
every entry gets region `JP`.

## What's on the disc

This is a Windows CE game. There is no `1ST_READ.BIN` program to search: the
game is `TYPE_E.EXE`, an SH-4 PE file with image base `0x10000`, started by
Windows CE (`0WINCEOS.BIN`). It reaches the VMU through `MAPLEDEV.dll`. The rest
of the disc is the bundled Dream Passport 3 browser (`2_DP.BIN`, `DPETC/`,
`DPTEX/`). Its `DPETC/VMS.DPS` and `DPTEX/VMSPARTS.PVR` sound like VMU art but
belong to the browser. The game's own bitmaps, `BMP_*` resources inside the
EXE and the `ET_*` folders, are full-size TV pictures, and `IMG_PARTS` is a
64×64 PVR texture.

With no screen in the archive to search for, the screens were found by trying
every 192-byte window of the EXE as a 48×32 1-bit screen and keeping the ones
that look like pictures. Six sit back to back in `.data` from `0x5BEC0` (file
offset `0x49CC0`), packed 1 bit per pixel (high bit first, 1 = lit) and turned
180°, the way the VMU's LCD takes them.

The routine at `0x48670` shows screen _n_ by sending `0x5BEC0 + 192 × n`, so
the screens are a numbered table:

| n   | Address   | Shows      | Archive entry |
| --- | --------- | ---------- | ------------- |
| 0   | `0x5BEC0` | Title logo | Title screen  |
| 1   | `0x5BF80` | ACCESS     | Access        |
| 2   | `0x5C040` | SAVE OK!   | Save OK       |
| 3   | `0x5C100` | SAVE NG!   | Save NG       |
| 4   | `0x5C1C0` | LOAD OK!   | Load OK       |
| 5   | `0x5C280` | LOAD NG!   | Load NG       |

A loop over the connected devices (`0x48244`) sends each VMU the logo;
what triggers that loop wasn't traced. The save and load code
(`0x19E00`–`0x1A630`) shows ACCESS while it works, then the result, then the
logo again. Every screen is shown somewhere, nothing animates, and there are no
sprites: every screen is drawn whole.

The 32 bytes at `0x5BEA0` and the 512 at `0x5B8A0`, just before the table, look
like the save file's icon palette and its 32×32 icon. They aren't LCD screens,
so they aren't in the archive.
