# Border Down

Scripts: `tools/disc-extraction/border-down/`.

Dump: Redump `Border Down (Japan)` (`.cue` and three `.bin` tracks; T-46703M
V1.000, 2003-08-13). The game was only released in Japan, so its pieces are
`ntsc-j`.

## What's on the disc

No file holds VMU art. Everything is in `1ST_READ.BIN`, which links Sega's
`pdLcd` library (version 2.00) and runs from `0x8C010000`. The art is stored a
byte a dot, 8 lit and 0 not, the form the library's LCD write takes, so a
search for 1,536-byte runs of only those two values found it.

| Screen      | Address      | Archive entry |
| ----------- | ------------ | ------------- |
| SDF logo    | `0x8C145ED4` | SDF logo      |
| TOTAL … HIT | `0x8C1825C8` | Hit counter   |

**SDF logo.** A whole screen, sent as it is: `0x8C137C18` (send to every VMU,
`r4` 0) is called with its address from four places (`0x8C07B5B6`,
`0x8C12779C`, `0x8C127C14` and `0x8C13781E`, the last in the memory card
code). Nothing writes into it.

**Hit counter.** During play the VMU counts hits. `0x8C127E60` prints the
value at `0x8C1D20F4` with `%4d` (`0x8C16C838`) and draws each character but
spaces from a table of ten digits (`0x8C16C7DC`, 10x12 each, indexed from
`'0'`) at y 10, x 1, 13, 25 and 37 of a second buffer, then sends it. Before
that, `0x8C127E3C` clears the buffer's rows 10–21; the rest is as on the disc,
TOTAL above and HIT below. The game loop at `0x8C1286D8` redraws it whenever
the count changes. The archive keeps the screen as the game draws it for a
count of 0, and the digits as a sprite font. Elsewhere the count is
multiplied by 5,000 (`0x8C0829A0`), so it plays into the score; what counts
as a hit wasn't traced.

Nothing animates.

## Save icons

The game writes one file, `BORDERDOWNDC` (7 blocks). The header builder
(`0x8C1379E0`) takes the VMU name ｹﾞｰﾑﾃﾞｰﾀ and description ＢＯＲＤＥＲ ＤＯＷＮ
ＤＣ from right after the file name (`0x8C1810D0` + 84 and + 93), the palette
from `0x8C145CB4` and one frame from `0x8C145CD4`, at speed 1: a red SDF
emblem. `vmu.py` rebuilds the header and it's imported with the disc as its
source.
