# Power Stone

Scripts: `tools/disc-extraction/power-stone/` (release `ps1`), shared with
[Power Stone 2](power-stone-2.md).

Dump: `Power Stone v1.020 (1999)(Capcom)(JP)[!][1MB1]` (`.gdi`).

The name and logo are the same in every release, so the game's own screens get
no region. Power Stone Mini's screens with Japanese text get `JP` (see
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

36 entries are whole 48×32 screens, all stills except the portraits, and one
is the Falcon course, a scroll (see [Falcon's course](#falcons-course)):

| Address                             | Archive title                                                             |
| ----------------------------------- | ------------------------------------------------------------------------- |
| `0xAD80`                            | Power Stone Mini title screen                                             |
| `0xAE40`, `0xAF00`                  | Capcom logo, Copyright (©1999)                                            |
| `0xCAA3`                            | Caution: replace the battery (JP)                                         |
| `0xA9B4`                            | Menu (JP)                                                                 |
| `0xAA74`+`0xAB34`                   | Falcon (intro, see [Portraits](#portraits))                               |
| `0xCCE3`+`0xCDA3`                   | Ayame (intro)                                                             |
| `0x8591`+`0x8651`                   | Gunrock (win)                                                             |
| `0xCB63`, `0xCC23`                  | Ayame's Shuriken Training stage, and (second)                             |
| `0x81DD`–`0x84D1`, `0x8C11`         | Gun-Gun Slots: medal get, quit?, double up?, match to double, great! (JP) |
| `0x8CD1`, `0x8D91`                  | Art museum opened, Music hall opened (JP)                                 |
| `0xB980`, `0xBA40`, `0xBB00`        | High score, one per game (JP)                                             |
| tables `0xBE80`, `0xC189`, `0xC492` | Rules: 4 pages Falcon, 4 Ayame, 8 Gun-Gun Slots (JP)                      |

The stored menu (`0xA9B4`) and the second stage screen (`0xCC23`) have no
direct address load in the code; they may be reached through computed
addresses, so they aren't marked unused.

### Portraits

Each character has two stored portraits, and the code plays them as a short
sequence, not a loop of two frames. The entries are those sequences, one frame
per tick of the game, at the same estimated 16 ms tick as
[Falcon's course](#falcons-course); each rests on the whole first portrait.

- **Falcon** (before his game): the portrait slides up from the bottom, two
  rows a tick (state 1 at `0x319E`: the top _c_ rows of `0xAA74` drawn at the
  bottom of the screen). It then flashes for 15 ticks (`0x3205`: a counter from
  16, and the screen sent inverted by `0x3CE1` while its bit 1 is set: 2 ticks
  inverted, 2 normal). Then the second portrait (`0x3212`, with a sound), held
  33 ticks (`0x3229`) before the game starts.
- **Ayame** (before her game): the same slide. Then for 31 ticks the two
  portraits swap every 2 ticks (`0x456C`: the first while the counter's bit 1
  is set), then the second, held 65 ticks (`0x4592`, `0x45A9`).
- **Gunrock** (when the slots pay): the first portrait for 24 ticks
  (`0x6B6E`), then it flashes (`0x6B9B`: inverted 3 ticks, then 4 normal, 4
  inverted, 4 normal, 4 inverted), then the second, with a sound, for 48 ticks
  (`0x6BD6`, `0x6BF3`). The game then goes back to the flash and repeats until
  the player moves on; the entry loops back to the first portrait instead. Over
  both, the win's payout label (`+50`, `×2`…) blinks at rows 12–18, 8 ticks on
  and 8 off (`0x7B28`); it depends on the win, so it's left out.

The slide-in draws over what was on screen before, which is taken as blank.
The intros are one-offs in the game, so their entries start with a second of
blank screen before each replay; the second is the archive's, not the game's.

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

38 sprites in `content/sprites/power-stone/`: the slot reels (48 symbols of
16×10, 16 per reel, a column per reel) with the payline the game ORs over them,
the payouts, coin, digits, 1000/2000 labels and BONUS TIME banner; a small 8×6
font with BET and $; Ayame's ninjas, shuriken, score popups and other sprites;
Falcon in eight flight poses, the CHECK banner, items, and the course as stored
(48×896); the READY/START/GAME OVER banners; and the menu headers,
items, arrows and high-score parts. Falcon's 16×8 item at `0x9FEA` is the same
pixels as Shuriken Training's `0x8F9D`, so it's kept once.

Not imported: the VMS file's own save icon (colour, for the Dreamcast's file
screen), the reel strip's order table, and the table after the course
(`0xE363`–`0xEA70`), which are data.

### Compared with Second Screen Archive

Second Screen Archive's
[Power Stone collection](https://second-screen-archive.neocities.org/power-stone-vmu-artwork-2)
(231 images) names each picture by its address in the same program, and the
layout is the same here. 141 of its images match this disc's bytes at their
address exactly. The rest:

- Its text screens (rules, slot prompts and rewards, menus, high scores,
  CAUTION, the copyright) are in English; this disc's are Japanese at the same
  addresses. Its copy looks to be from a Western release, whose English
  screens aren't in the archive yet.
- 23 Ayame and Falcon sprites are exactly the image bytes of this disc's masked
  rows, without the mask (checked for all 23).
- 22 are screens it assembled (slot reels, menus), not stored art.

Its coin starts at `0x815F`, a row after where the code's pointer table puts it
(`0x815D`, whose first row is blank).
