# Power Stone

Scripts: `tools/disc-extraction/power-stone/` (release `ps1`), shared with
[Power Stone 2](power-stone-2.md).

Dump: `Power Stone v1.020 (1999)(Capcom)(JP)[!][1MB1]` (`.gdi`).

The name and logo are the same in every release, so the game's own screens get
no region. Power Stone Mini's screens with Japanese text get `ntsc-j` (see
[Power Stone Mini](#power-stone-mini)).

## What's on the disc

No file holds VMU art. The game keeps two screens in `1ST_READ.BIN`, which loads
at `0x0C010000` (the `0x0C` alias of main RAM, like Moero! Justice Gakuen), so
`common/find_code.py` can't see their references.

They were found by searching for the archive's title screen, which matched only
with its bits inverted. Each screen has a routine that turns it into a byte
buffer (8 = lit) for the VMU, and the routine sets the polarity.

| Screen | Address      | Routine      | Stored   | Archive entry                                |
| ------ | ------------ | ------------ | -------- | -------------------------------------------- |
| Title  | `0x0C17C198` | `0x0C020174` | inverted | Title screen (already in the archive, exact) |
| ACCESS | `0x0C17C258` | `0x0C0201BC` | as shown | Access                                       |

Both routines have many callers in the save and load code, so every screen is
shown. Nothing animates.

The archive's Power Stone title came from a screenshot, through an older version
of the importer that read a screenshot's majority colour as unlit. It got this
one right: the disc stores the title inverted, and the game inverts it again
before sending it, so the entry matches the disc exactly.

## Power Stone Mini

Power Stone carries a whole VMU game, パワーストーン ミニ (Power Stone Mini),
for the player to download to a VMU: Falcon's Aerial Adventure, Ayame's
Shuriken Training and Gunrock's Gun-Gun Slots. Its reward screens announce the
art museum and music hall opening in the main game's Omake mode. It has no file of its own: it's a
64 KiB VMS image inside `1ST_READ.BIN`, at offset `0x15BB98`, found by its
header (the description at `+0x200` is `ﾊﾟﾜｰｽﾄｰﾝﾐﾆ`). Its code runs to
`0x7FD0`; the art fills `0x7FDB`–`0xE363`, and a table (likely the Falcon
course's layout) runs on to `0xEA70`. Addresses here are offsets into that
image.

Extracted by `tools/disc-extraction/power-stone/mini.py` from the Redump dump
`Power Stone (Japan)`, the same build as v1.020: the title and ACCESS screens
above sit at the same offsets.

**Format.** Plain 1 bit per dot, high bit first, upright, whole bytes per row.
The program reads it with `LDC` through TRH/TRL, so most addresses come straight
from `mov #hi,trh` / `mov #lo,trl` in the code, with the row count and bytes
per row loaded next to them (`common/lc86k.py` reads it). Two twists:

- **Masked sprites.** Sprites drawn over a background store each row as the
  mask's bytes, then the image's; the game does `and mask` then `or image`, so a
  mask bit of 0 is the sprite's area. Each is kept as two sprites, the image and
  its mask (shown lit where the sprite is opaque).
- **Pre-shifted copies.** A sprite that moves sideways has a table of eight
  pointers, the art shifted right by 0–7 dots, picked with `x & 7` (at
  `0x4A7B` for Ayame's score popups). Copy k is copy 0 shifted by k in all 29
  tables (copy 7 of a masked 16-dot sprite is stored 24 dots wide, read by its
  own routine at `0x4ADA`), so only copy 0 is kept.

The Ayame stage background (`0xCB63`) is drawn as stored at `0x4BE6`, and
inverted (`xor #0xff`) at `0x4BAE`, a flash.

### Screens

39 entries are whole 48×32 screens, all stills, and one is the Falcon course,
a scroll (see [Falcon's course](#falcons-course)):

| Address                             | Archive title                                                             |
| ----------------------------------- | ------------------------------------------------------------------------- |
| `0xAD80`                            | Power Stone Mini title screen                                             |
| `0xAE40`, `0xAF00`                  | Capcom logo, Copyright (©1999)                                            |
| `0xCAA3`                            | Caution: replace the battery (JP)                                         |
| `0xA9B4`                            | Menu (JP)                                                                 |
| `0xAA74`, `0xAB34`                  | Falcon, Falcon (second) (see [Portraits](#portraits))                     |
| `0xCCE3`, `0xCDA3`                  | Ayame, Ayame (second)                                                     |
| `0x8591`, `0x8651`                  | Gunrock, Gunrock (second)                                                 |
| `0xCB63`, `0xCC23`                  | Ayame's Shuriken Training stage, and (second)                             |
| `0x81DD`–`0x84D1`, `0x8C11`         | Gun-Gun Slots: medal get, quit?, double up?, match to double, great! (JP) |
| `0x8CD1`, `0x8D91`                  | Art museum opened, Music hall opened (JP)                                 |
| `0xB980`, `0xBA40`, `0xBB00`        | High score, one per game (JP)                                             |
| tables `0xBE80`, `0xC189`, `0xC492` | Rules: 4 pages Falcon, 4 Ayame, 8 Gun-Gun Slots (JP)                      |

The stored menu (`0xA9B4`) and the second stage screen (`0xCC23`) have no
direct address load in the code; they may be reached through computed
addresses, so they aren't marked unused.

### Portraits

Each character has two portraits, kept as separate stills. The game shows them
in short sequences, read from the code below; those aren't kept as animations.
The ticks they count weren't timed (an estimated 16 ms; see
[Falcon's course](#falcons-course)). The six addresses are loaded only where
listed here, and no pointer table holds them.

- **Falcon**, during his game, each time a counter (`0xA9`) reaches 3
  (`0x2660`), likely three Power Stones: the first portrait slides up from the
  bottom of the screen, two rows a tick, over the game (`0x319E`), flashes
  inverted for 15 ticks (`0x3205`; `0x3CE1` sends the screen inverted), then
  the second appears with a sound and stays 33 ticks (`0x3212`, `0x3229`).
  Play resumes in a timed powered-up state that redraws the course.
- **Ayame**, during her game, each time a counter (`0x8C`) reaches 3
  (`0x441E`, `0x4867`): the same slide, then the two swap every 2 ticks for 31
  ticks, then the second stays 65 ticks (`0x456C`–`0x45A9`). It ends by adding
  a flower shuriken (花シュリケン) to her stock (`0xD4` bits 5–7, `0x45B5`),
  which her rules page ties to Power Stones.
- **Gunrock** is the slot game's host. The first portrait shows on a win for
  24 ticks with the payout label (`+50`, `×2`…) blinking over it (state
  `0x36`, `0x6B6E`; the label at `0x7B28`), and during Bonus Time it alternates
  with the Bonus Time screen before each spin (`0x6235`). On the other kind of
  win (state `0x39`, entered at `0x6970` and `0x6A97`) it flashes, inverted 3
  ticks, then 4 normal, 4 inverted, 4 normal, 4 inverted (`0x6B9B`); then the
  second portrait appears with a sound and stays 48 ticks with the label
  blinking (`0x6BF3`) before the next spin.

None of them loops: each sequence runs once per trigger, and the game draws
over the second portrait when it ends.

![Falcon's sequence](../../public/notes/power-stone/falcon.gif 'Falcon')
![Ayame's sequence](../../public/notes/power-stone/ayame.gif 'Ayame')
![Gunrock's flash win](../../public/notes/power-stone/gunrock.gif 'Gunrock, flash win')

_Rebuilt from the code above, not captured: Falcon, Ayame, and Gunrock's flash
win. Each step's length is counted in ticks at the estimated 16 ms, rounded to
GIF's hundredths of a second. The slide-ins start from a blank screen, where
the game has its own screen behind them; Gunrock's blinking payout label is
left out; and the second of blank before each replay is ours, since the game
plays them once. `mini.py` writes them._

### Falcon's course

Falcon's Aerial Adventure scrolls its course down the screen as Falcon flies
up. The routine at `0x34EE` keeps a position (`0x8D:0x8E:0x8F`, in 1/256 rows)
and adds the speed to it every tick (`0x83:0x84`: it starts and cruises at 1
row, the accelerator takes it to 3 and the brake to 0.5). It then draws the 32
rows that start `position % 128` rows above the bottom screen of section
`position / 128 % 18`, whose addresses are a table at `0x34CA`:
`0xE2A3` five times, `0xDFA3`, `0xDCA3` five times, `0xD9A3`, `0xD6A3` five
times, `0xD3A3`. So a lap is three stretches of road, each repeated five times,
joined by three transitions: 2,304 rows, whose end meets its start.

The course isn't built from tiles: it's one stored picture, 48×896, kept as the
"Aerial Adventure: course" sprite, and a lap replays parts of it in that order.
A part covers the 128 rows the window climbs through plus the 32-row screen it
ends on, counted in the stored picture from its top (`0xCE63`, 6 bytes a row):

| Part of the lap  | Section  | Stored rows | Times |
| ---------------- | -------- | ----------- | ----- |
| Road 1           | `0xE2A3` | 737–895     | 5     |
| Into road 2      | `0xDFA3` | 609–767     | 1     |
| Road 2           | `0xDCA3` | 481–639     | 5     |
| Into road 3      | `0xD9A3` | 353–511     | 1     |
| Road 3           | `0xD6A3` | 225–383     | 5     |
| Back into road 1 | `0xD3A3` | 97–255      | 1     |

Each section sits 128 rows above the one before, so moving on to the next part
just keeps climbing the picture. A road's repeats jump back down 128 rows, and
show no seam because each road repeats every 128 rows; the lap wraps cleanly
because stored rows 96–127 are the same as road 1's bottom screen (864–895).
All three are checked against the stored rows.

For example, at position 300 the game is in part 300 / 128 = 2 (the third of
road 1's five), 300 % 128 = 44 rows into it: it draws stored rows 820–851, the
32 rows that start 44 above that part's bottom screen (rows 864–895). The
course scroll in the grid plays this lap.

It's in the archive as a downward scroll of one lap: a 48×2,335 strip whose
windows are exactly what the game draws at each of the 2,304 positions
(checked for every one). It moves 1 row a step, the cruising speed, every 16
ms. That interval is an estimate: timer 0 is set up at `0x1677` (prescaler
`0xF5`, reload `0xF8`), about 62 Hz if it counts the 32.768 kHz crystal's
cycle clock, but that it paces the game loop wasn't traced. The table never
reaches the course's first 97 stored rows (`0xCE63`–`0xD0A9`); the stored
course, those rows included, is also kept as a sprite.

The menus the game shows are composed at run time: a 48×8 header, a 40×24 item
at (0, 8) and an 8×24 arrow column at (40, 8). Their parts are kept as sprites
rather than guessing which combinations appear.

### Sprites

52 sprites in `content/sprites/power-stone/`, one per bitmap the program
stores, or per run of bitmaps stored back to back, their frames one under the
next in stored order with each frame's size in `glyphs`. Nothing is laid out
side by side; `mini.py` checks each table it follows, and every plain sprite is
its bytes in the program.

- Gun-Gun Slots: the 48 reel symbols (16×10, reel by reel, from `0x8811`); the
  payline the game ORs over them (`0x8711`), a whole 48×32 bitmap kept as a
  sprite tagged `overlay`; the 7 payouts (48×7 from `0x7FEF`, which the table
  at `0x7FDB` points at, some more than once); the coin's 4 frames and the 10
  digits, through tables at `0x8155` and `0x829D`, stored 16 rows tall with the
  last rows blank; 1000 and 2000; BET, $ and the BONUS TIME banner.
- The small font, below.
- Shuriken Training: Ayame's ninjas, shuriken, score popups and other sprites.
  Where the game keeps a sprite as a table of 8 copies pre-shifted 0–7 dots,
  only copy 0 is kept; where an animation has a table per frame, copy 0 of
  each is stacked. Masked sprites are an image and a mask.
- Aerial Adventure: Falcon's 8 flight poses, the CHECK banner, four items
  stored apart, a 24×18 sprite and the course as stored (48×896). Falcon's 16×8
  item at `0x9FEA` is the same pixels as Shuriken Training's `0x8F9D`, so it's
  kept once.
- Shared interface: the 5 banners (READY, START and the rest, back to back from
  `0xAC60`; the first two are stored 9 rows tall with a line under them, but
  the code draws 8 rows of each); 7 menu headers, each stored on its own (the
  two START headers are the same pixels, so one is kept); the menu items in
  the runs they're stored in (an empty frame, the main menu's 4, the
  minigames' 13, sound on/off's 3), the arrows, and the high-score parts (a
  40×19 frame and three 8×19 pieces).

An earlier import grouped many of these by theme and laid them side by side,
which hid how they're stored, cut the coin and digits short, and lost the
banners' bottom lines.

The small font is 27 characters of 8×6 at `0x8E7B`, 6 bytes each, kept as
stored: one under the next. It runs from the end of BONUS TIME to the start of
the sight's table. The code reads glyphs 0–2 directly, blank and three dot marks
(3–6) at `0x8E8D` + 6n, and the digits twice: in the right half of the byte at
`0x8EA5` + 6n (7–16) and in the left half at `0x8EE1` + 6n (17–26), so two can
be ORed into one byte. BET (`0x813D`) and $ (`0x8149`) are separate sprites,
read on their own by the slots. An earlier import laid all of these side by
side in 8-pixel slots, which cut BET to its left half under the $.

Not imported: the VMS file's own save icon (colour, for the Dreamcast's file
screen), the reel strip's order table, and the table after the course
(`0xE363`–`0xEA70`), which are data.
