# Vampire Chronicle for Matching Service

Scripts: `tools/disc-extraction/vampire/`.

Dump: Redump `Vampire Chronicle for Matching Service (Japan)` (`.cue` and
three `.bin` tracks). The game was only released in Japan, so its pieces are
`ntsc-j`.

## What's on the disc

No file holds the VMU screens (`DPETC/VMS.DPS` belongs to the bundled Dream
Passport browser, as in Marvel vs. Capcom 2). Four screens sit back to back in
`1ST_READ.BIN`, which runs from `0x8C010000`, stored as shown (1 bit a dot,
high bit first, 1 = lit).

| Screen | Address      | Archive entry  |
| ------ | ------------ | -------------- |
| Logo   | `0x8C227BF4` | Title screen   |
| ACCESS | `0x8C227CB4` | Access         |
| OK!    | `0x8C227D74` | OK (unused)    |
| ERROR! | `0x8C227E34` | Error (unused) |

The VMU code is Marvel vs. Capcom 2's, as in Capcom vs. SNK. Every caller
loads a screen's address into `r4` and calls `0x8C0AAE3A`, which spreads its
bits into a byte buffer at `0x8C2275F4` (8 for a 1 bit, 0 for a 0 bit) for the
library's LCD write. Nothing inverts, so the screens show as stored: the logo
and the frame around the words are mostly lit dots. The routine has six
callers, all in the memory card code (`0x8C0AA67C`–`0x8C0AAD7C`): four pass
the logo and two ACCESS. Nothing loads OK! or ERROR!, by address or by an
offset from the others, so they're kept as unused. Nothing animates.

The buffer isn't empty on the disc. Its 1,536 bytes hold a smiling face drawn
in lines, left over from the build. The game fills the buffer before every
send, so it's never shown, and it isn't kept.

## Save icons

The header builder (`0x8C0AAEE0`) has two save types. It copies the VMU name,
description and a 16-byte code after them for each, then the palette from the
pointers at `0x8C2275E4` and the frame from `0x8C2275EC`, one frame at
animation speed 5.

| Type | Memory card name | VMU name          | Palette      | Frame        | Archive entry                    |
| ---- | ---------------- | ----------------- | ------------ | ------------ | -------------------------------- |
| 0    | `VAMPIRE_.SYS`   | ｳﾞｧﾝﾊﾟｲｱｾｰﾌﾞﾃﾞｰﾀ  | `0x8C2271A4` | `0x8C2271E4` | Save file (from the disc)        |
| 1    | `CAP_NET_.NET`   | `CAP-NET_NETﾌｧｲﾙ` | `0x8C2271C4` | `0x8C2273E4` | Marvel vs. Capcom 2's, identical |

The save's description is ヴァンパイア ｸﾛﾆｸﾙ セーブデータ. The Capcom network
file's icon is byte for byte the one in Marvel vs. Capcom 2, so the archive
keeps it once, there.
