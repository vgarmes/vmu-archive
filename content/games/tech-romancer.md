# Choukou Senki Kikaioh

Scripts: `tools/disc-extraction/kikaioh/`.

Dump: Redump `Choukou Senki Kikaioh (Japan)` (`.cue`), T-1206M, V1.003, dated
1999-11-18 in its IP.BIN. The archive files it under Tech Romancer, its US and
European title.

The game's own two screens carry the Japanese logo, and most of Kikaioh Mini's
screens have Japanese text, so those get `ntsc-j`. Kikaioh Mini's screens in
English (the Capcom logo, the copyright, the money won) get no region.

## What's on the disc

`1ST_READ.BIN` (loading at `0x8C010000`) holds the save file's descriptor at
`0x8C160CE8`: its VMS description, ｷｶｲｵｰ ｾｰﾌﾞﾃﾞｰﾀ, its Dreamcast one,
キカイオー　セーブデータ, then two screens of 192 bytes stored upright in the
archive's own encoding (1 bit per pixel, high bit first).

| Screen | Address      | Archive entry |
| ------ | ------------ | ------------- |
| Logo   | `0x8C160D28` | Title screen  |
| ACCESS | `0x8C160DE8` | Access        |

`0x8C014066` sends one of them to every VMU (ports A to D, both slots): the logo
when its first argument is 0, ACCESS otherwise. `0x8C0141B8` does the same for
one VMU. Both have many callers in the save and load code, so both screens are
shown. Nothing animates.

## Save icons

Both save icons in the archive came from US saves, and both are on this disc
byte for byte, palette included:

- the save file's (`ROMANCER DATA`; `KIKAIOH__DAT` in Japan) at `0x8C160AC8`
  in `1ST_READ.BIN`, right before the descriptor above;
- Kikaioh Mini's three frames at `0x260` in `/GAME/KIKAIOH.BIN`, in the VMS
  header of the minigame (`TECHROMANCER` in the US, `KIKAIOH___VM` here).

So the Japanese release writes the same icons.

## Kikaioh Mini

The game carries a VMU game, キカイオー ミニ (Kikaioh Mini, Tech Romancer Mini in
the US), in its own file, `/GAME/KIKAIOH.BIN`: a whole VMU program of 63341
bytes, with its VMS header at `+0x200`, that the game writes to the memory card
as `KIKAIOH___VM`. It has three games, Love & Punch, Mugen Gattai!! (夢幻合体!!)
and Janken Fight! (じゃんけんファイト!), and keeps your money (G) and high
scores. It is Capcom's Power Stone Mini engine: the same timer setup, the same
drawing routines, and two screens pixel for pixel the same as other Capcom
games' (the Capcom logo is Power Stone Mini's, the low battery CAUTION is
Marvel vs. Capcom 2's), so those two aren't stored twice.

Addresses below are offsets into the program, which is how the VMU's CPU sees
its flash. All the art is plain 1 bit per dot, high bit first, upright.

### Screens

The program draws whole screens two ways, both taking the art's address in
TRH:TRL: `0x0DC3` copies 192 bytes straight to the LCD, and `0xAE57` copies
them into a 192-byte buffer in work RAM that is then sent to the LCD.
`0xAE57` is a case of `0xA8F7`, which copies any width and height into that
buffer (`0xA92A` ORs, `0xA95F` ANDs, for sprites with masks).

| Shows                         | Address  | Drawn by |
| ----------------------------- | -------- | -------- |
| CAUTION (replace the battery) | `0xA81D` | `0x0DC3` |
| CAPCOM                        | `0x8CC8` | `0x0DC3` |
| © CAPCOM 2000                 | `0x8D88` | `0x0DC3` |
| Title (a strip, see below)    | `0x8BE4` | `0x0DC3` |
| GREAT!! 5000G GET!            | `0x4421` | `0x0DC3` |
| TOTAL … G GET!!               | `0x44E1` | `0x0DC3` |
| … G GET!!                     | `0x5AF0` | `0xAE57` |
| GREAT!! 10000G GET!           | `0x5BB0` | `0xA8F7` |
| Money held (現在の所持金)     | `0x9CF0` | `0xAE57` |
| High score: Love & Punch      | `0x9880` | `0xAE57` |
| High score: Mugen Gattai!!    | `0x9940` | `0xAE57` |
| High score: Janken Fight!     | `0x9A00` | `0xAE57` |

The money and score screens are drawn with their numbers left blank; the game
writes the digits over them.

The title: `0x12B9` shows the 192 bytes at `0x8BE4`, then `0x12CF` moves the
start down a row (6 bytes) a tick until it reaches `0x8C08`, six rows on, and
waits there for A and B. The logo rises and PRESS: A+B comes up under it. The
archive keeps the seven positions as frames, the last held for the playback's
sake (the game holds it until you press A and B).

The rules: `0x1D49` picks one of three lists of big-endian pointers ended by a
0 byte (`0x9E40`, `0xA149`, `0xA390`) and shows a page a button press. Love &
Punch has 4 pages, Mugen Gattai!! 3, Janken Fight! 6, stored back to back after
their lists.

### The main menu

The menu is built in the work RAM buffer (`0x134E`): `0x1424` copies the
メニュー header (48x8, `0x8E48`) to rows 0 to 7, `0x1451` copies rows 2 to 20 of
the selected item to rows 10 to 28, `0x1487` ORs a frame (40x24, `0x8E78`) over
rows 8 to 31, and `0x14EA` puts an arrow (8x24) in the right-hand column. The
four items are 40x24 each, one under the next from `0x8F38` (a fifth copy of the
first closes the loop), and moving between them slides that strip 2 rows a tick
(`0x156F`). The archive has the four resting screens. Resting, the arrow steps
through `0x8EF0`, `0x8F08`, `0x8F20` and back to the first every 7 ticks: the
menu adds 1 to a counter each tick and the arrow routine adds 1 more when it
runs, every eighth count.

### Timing

Estimated, as for Power Stone Mini: timer 0's high byte (prescaler `0xF5`,
reload `0xF8`, set at `0x1134`) interrupts about 62 times a second if it counts
the 32.768 kHz crystal's cycle clock, and the main loop (`0x11AE`) wakes on its
handler (`0x0052`). So a tick is taken as 16 ms.

### Not yet extracted

- The sub-menus (the minigame and high score choices, and the sound menu).
  They are built like the main menu around strips of 40x24 items that slide,
  with the mini ゲーム, ハイスコア and サウンド headers; the minigame choice
  has a locked `?` item.
- The start and how-to-play menu (スタート, アソビカタ).
- The three games' own art: Janken Fight!'s fighters (24x32 halves through the
  tables at `0x4A0E` to `0x4A3E`), the portraits, the rock, paper and scissors
  hands, WIN, LOSE and GAME OVER, GET READY, GO!, TIME OVER and TOTAL banners,
  the stage lists and the digits. The games draw these with routines of their
  own, straight to the LCD, so each needs its size read from its routine.
