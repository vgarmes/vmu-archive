# Napple Tale: Arsia in Daydream

Scripts: `tools/disc-extraction/napple-tale/`.

Dump: Redump `Napple Tale - Arsia in Daydream (Japan)` (`.cue` and three
`.bin` tracks; HDR-0079 V1.006, 2000-09-25). The game was only released in
Japan, so its pieces are `ntsc-j`.

## What's on the disc

No file holds VMU art; the `ETC` files are textures, event scripts and the
game's initial memory. Everything is in `1ST_READ.BIN`, which runs from
`0x8C010000`. It doesn't link `pdLcd`: its own LCD write (`0x8C114300`)
takes a screen a byte a dot.

### Screens

Six screens, a byte a dot (255 lit, 0 not), back to back from `0x8C0FC6C0`
(a few of the game's variables sit just before them). They were found by
searching the program for 1,536-byte runs of two values. The send
(`0x8C032886`) writes screen n from `0x8C0FC6C0 + n × 1536`, or, for n < 0,
a work buffer at `0x8C2E6B2C`.

| Screen | Text             | Shown                                                               | Archive entry    |
| ------ | ---------------- | ------------------------------------------------------------------- | ---------------- |
| 0      | Napple Tale logo | `0x8C01841A` copies it into the buffer at `0x8C2E4270` and sends it | Napple Tale logo |
| 1      | セーブ中デス！   | `send(1)`                                                           | Saving           |
| 2      | ロード中デス！   | `send(2)`                                                           | Loading          |
| 3      | OKデス!!         | `send(3)`                                                           | OK               |
| 4      | 失敗デス         | `send(4)`                                                           | Failed           |
| 5      | 使用中デス！     | `send(5)`                                                           | In use           |

### Score display

The game also writes text to the VMU. `0x8C018360` draws a string at a
column and row (4 dots by 6) into the same byte-a-dot buffer at
`0x8C2E4270`, which the display clears first, and `0x8C018742` sends it. Its one
caller, `0x8C076A34`, is a score display with several modes (0 to 4, 98 and
99), printed from these strings:

- `TM   %02d:%02d` or `TM   --:--`, a time counted in steps of 30 ticks,
  rolling over at 60;
- `COMBO %4d`, `+%4d`, `+%5d` and `%5d`;
- `TIME BONUS`, then `NEW RECORD!!` or ` TRY AGAIN!!`;
- `HI %7d` and `SC %7d` on the top two lines.

One mode also draws gauges, from a chain of comparisons. These screens are
drawn from live values, so they aren't in the archive yet.

The font is at `0x8C0FEADC`: 96 characters from space on, 3 bytes each, each
byte two rows of 4 dots (high nibble first), so 4×6. Space to `_` are
upper-case ASCII; the 32 slots after them hold small graphics instead of
lower-case letters. It's kept as the Score display font sprite;
`vmu.py` rebuilds the disc's bytes from it.

## Save icons

The game writes two saves, each with one frame at speed 1. Both use the same
frame (`0x8C101130`) with their own palette:

| Save           | Built at     | Palette      | VMU name      | Archive entry |
| -------------- | ------------ | ------------ | ------------- | ------------- |
| `NAPPLE_T.000` | `0x8C033160` | `0x8C1010F0` | ﾅｯﾌﾟﾙ ﾌｧｲﾙ*n* | Game file     |
| `NAPPLE_T.SYS` | `0x8C03354A` | `0x8C101110` | ﾅｯﾌﾟﾙ ｼｽﾃﾑ    | System file   |

Both carry the description ナップル・テール. The game file's name holds its
slot number (ﾅｯﾌﾟﾙ ﾌｧｲﾙ%d); the archive's header is rebuilt with slot 1.
The game also reads a `NAPPLE_T.DLD` (`0x8C035C2A`), but never writes one,
so its icon isn't on the disc.
