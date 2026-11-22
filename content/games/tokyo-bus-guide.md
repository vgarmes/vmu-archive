# Tokyo Bus Guide

Scripts: `tools/disc-extraction/tokyo-bus/`.

Dump: Redump `Tokyo Bus Guide (Japan) (Rev A)` (`.cue` and three `.bin`
tracks; T-35402M V2.000, 2000-01-06). The game was only released in Japan, so
everything from it is `ntsc-j`.

The disc carries two kinds of VMU art: three screens the game itself sends
while you play, and a whole VMU program, a traffic sign quiz (交通標識クイズ),
that it writes to the memory card.

## The game's screens

Three files in `/SYSTEM` (the six `*_COMMON` folders hold the same files byte
for byte): a little-endian frame count, then 48x32 frames at a byte a dot
(`0x0F` lit, 0 not), stored as shown.

| File              | Frames | Archive entry |
| ----------------- | ------ | ------------- |
| `VM_BUS.LCD`      | 2      | Bus           |
| `VM_DANGER.LCD`   | 1      | Danger        |
| `NOW_LOADING.LCD` | 1      | Now loading   |

`1ST_READ.BIN` loads each into a small record, `{data, 10, frame}`
(`0x8C22622C`, `0x8C226238`, `0x8C226244`), listed in that order at
`0x8C044FBC` with a null fourth. `0x8C01C92C` picks one by number (3 sends a
blank screen) and `0x8C01C940`, called from the game's loops, sends it to every
VMU through `0x8C01BB78`. That keeps a shared count (`0x8C226318`) and moves to
the next frame once it has reached the record's 10, so each frame is held 11
calls. At one call per 60 Hz frame that's 183 ms a frame, which is what the bus
plays at; a capture would settle it. The game picks the bus, Danger and the
loading screen from several places each; which situations those are wasn't
traced.

## Traffic sign quiz

`/SYSTEM/PDAQUIZ.BIN` (22,852 bytes) is a VMU program with its VMS header at
`0x200`: QUIZ GAME, 東京バス案内 交通標識クイズ. The game's memory card menu
offers to download it (it needs 45 blocks) and writes it as `TOKYOBUS._VM`;
it can also add points to it. Its colour icon, a winding road sign, is in the
archive from the disc.

Its art is read through an image table at `0x2BD6`: 67 big-endian pointers to
entries of width, height and bytes a row, then up to nine big-endian frame
pointers ending in 0, 1 bit a dot (high bit first, 1 = lit). `0x10EC` draws
an entry's frame at a position the caller sets.

| Entry | Size  | Frames                              | Archive                          |
| ----- | ----- | ----------------------------------- | -------------------------------- |
| 0–62  | 32x32 | one each, `0x3656`–`0x55D6`         | sprites: sign 00–62              |
| 63    | 48x32 | blank (`0x14B0`), title, no battery | screens: title, no battery       |
| 64    | 24x7  | eight pieces of the credits ticker  | drawn on the title               |
| 65    | 3x5   | blank, right arrow, left arrow      | sprites: right arrow, left arrow |
| 66    | 15x15 | circle, cross                       | sprites: circle, cross           |

The 63 signs are Japanese road signs (no entry, speed limits, 止まれ, pedestrian
crossing, falling rocks, deer…), numbered by their place in the table.

Text is drawn with an 8x8 font at `0x2DE8`, 192 glyphs (kept as one sprite):
a code below `0x80` is its own glyph, one above draws glyph code − `0x20`.
That gives ASCII, then katakana with dakuten and handakuten, then the
half-width katakana of JIS X 0201 at their Shift-JIS codes. Screens of text
are lists of records, y, x, then the codes, ending in `0xFF`.

**Title.** `0x18E8` draws entry 63's title (a bus at a bus stop, PRESS A+B),
then three pieces of the credits ticker along the top row, 24 dots apart:
"TOKYO BUS GUIDE ©FORTYFIVE 1999", round and round. The loop at `0x18AE` moves
the ticker 8 dots left each tick, and a piece on after three (`BNE #0xE9`
sets the carry below it), until A+B. A tick is the base timer's interrupt 1
(`0x0A00`, counting down `0x033`), which the program sets up with BTCR bit 7
clear: once every 16,384 cycles of the 32.768 kHz crystal, half a second. So
the title is 24 frames of 500 ms.

**No battery.** デンチガ アリマセン ("no battery") with a battery mark, drawn
whole by `0x0CF2` when port 7 reports low voltage.

**Version.** `0x1887` clears the screen and writes "PDAクイズ" and "0.90"
(`0x189D`), but nothing calls it. Kept as unused.

The menus aren't in the archive yet: they're drawn from text records with
cursors and numbers filled in at run time (`0x1972`, `0x19A4` and on). They
say ゲーム, ポイント, サウンド; ハード, ノーマル, イージー; サウンド ON/OFF;
リトライ? YES/NO; and after a question セイカイ, ハズレ, ガンバレ, グレイト and
パーフェクト, with the score.

## Save icons

- **Save file** (`TOKYOBUS.001`–`.010`, 東京バス案内 データ): already in the
  archive from a dumped save. The game builds it from `/SYSTEM/BUS_MEM.VMI`,
  which despite its name is just the icon, a palette and one 32x32 frame;
  they match the archive's entry byte for byte.
- **Traffic sign quiz** (`TOKYOBUS._VM`): the program's own header, imported
  from the disc.
