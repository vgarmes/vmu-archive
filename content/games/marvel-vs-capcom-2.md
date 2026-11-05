# Marvel vs. Capcom 2

Scripts: `tools/disc-extraction/mvc2/`.

Dump: `Marvel vs. Capcom 2 - New Age of Heroes (Japan)` (Redump, `.cue`). The
logo is the same in every release, so the game's own screens get no region.

## What's on the disc

No file holds the game's VMU screens (`DPETC/VMS.DPS` belongs to the bundled
Dream Passport browser, as in Street Fighter III 3rd Strike). Two screens sit
back to back in `1ST_READ.BIN`, which runs from `0x8C010000`, found by
searching for the archive's title screen: it matched only with its bits
inverted.

| Screen | Address      | Stored   | Archive entry                       |
| ------ | ------------ | -------- | ----------------------------------- |
| Title  | `0x8C190CE4` | as shown | Title screen (corrected, see below) |
| ACCESS | `0x8C190DA4` | as shown | Access                              |

Every caller loads one of the two addresses into `r4` and calls
`0x8C1257C0`, which spreads the screen's bits into a byte buffer at
`0x8C1906E4` (8 for a 1 bit, 0 for a 0 bit), then `0x8C125806` sends the buffer
through the library's LCD write (`0x8C19FC9C`). The library packs a byte with
bit 3 set as a lit dot (`0x8C1AD772`). The flag it's given (0 or 3, from a
query of the device) picks one of four packers, which only differ in the
direction they lay the dots out; none inverts. So the VMU shows both screens as
stored: the title is a light logo on a dark screen, and ACCESS is dark on light.
The title is loaded from eight places and ACCESS from five, all in the memory
card code (`0x8C125AA6`–`0x8C128696`); what picks one wasn't traced, the names
say when they show. Nothing animates.

**The title was the wrong way round.** The archive's title came from a
screenshot of the US release, through the same older importer that read a
screenshot's majority colour as unlit (see [Power Stone](power-stone.md)). On
a mostly dark screen that inverts every dot. Power Stone's title came out
right only because that game inverts its title before sending it; this one
doesn't. The entry now holds the disc's bytes, which are the screenshot's
exactly, inverted, and has no region, since this Japanese disc has the same
logo.

The buffer isn't empty on the disc. Its 1,536 bytes hold the bottom of a
screen as the routine would leave it, the letters "VS4" (the name of the
VS.COM program's file, below), left over from the build. The game fills the
buffer before every send, so it's never shown, and it isn't kept.

## Save icons

The game builds each save's header from a table in `1ST_READ.BIN`
(`0x8C127188`, by file type): the VMU name and description from `0x8C190E64`
on, the palette from the pointers at `0x8C191058` and the one frame from
`0x8C191A6C`, at animation speed 5. The memory card names are at `0x8C164994`.

| Type | Memory card name | Palette      | Frame        | Archive entry                       |
| ---- | ---------------- | ------------ | ------------ | ----------------------------------- |
| 0    | `MVLVS.C2__UP`   | `0x8C190FB8` | `0x8C19106C` | UPLOAD file (from the disc)         |
| 1    | `MVLVS.C2_SYS`   | `0x8C190FD8` | `0x8C19126C` | System file (confirmed)             |
| 2    | `MVLVS.C2__VM`   | `0x8C190FF8` | `0x8C19146C` | VS.COM file (confirmed)             |
| 3    | `MVLVS.C2_DOW`   | `0x8C191018` | `0x8C19166C` | DOWNLOAD file (from the disc)       |
| 4    | `CAP_NET_.NET`   | `0x8C191038` | `0x8C19186C` | Capcom network file (from the disc) |

The names are matched to the types by what they say; the header builder takes
the type, not the name.

- **Confirmed.** The two icons already in the archive, read from dumped saves,
  are the game's own: the System file's palette and frame, and the VS.COM
  file's, match the table byte for byte.
- **From the disc.** UPLOAD, DOWNLOAD and the Capcom network file (CAP-NET,
  カプコン ネットワークファイル) have no dumped save in the archive. `vmu.py` rebuilds
  each header as the game does and they're imported with the disc as their
  source. They're kept as `ntsc-j`, as their names are.
- Type 2, VS.COM, takes nothing from the table: the file is `VS4.BIN`, a VMU
  program with its own header (`MVS.C2_VS.COM`), whose three frames are
  three copies of the table's type 2 frame. The dumped VS.COM save in the
  archive is named `M_VS_C2` on its memory card, not `MVLVS.C2__VM` as this
  disc would name it; where that name comes from isn't known.
- The name table also holds `ICONDATA_VMS`, but the header builder has no case
  for it and no sixth icon follows the five, so the game makes no memory card
  icon of its own.

## VS.COM

The disc's root holds a VMU program, `/VS4.BIN` (28,646 bytes), with its VMS
header at `0x200` (`MVS.C2_VS.COM`). The game writes it to the memory card as
the VS.COM file, with the player's data at `0x0A00`, which the program copies
into RAM at start (`0x5932`). On the VMU it's a companion to the save: a Capcom
logo, the copyright and a title waiting for A+B, then a menu of Level and Exp.,
points, a VS shop (characters, colours and stages bought with points), the
player's characters, a stage list, play time, net rank and sound settings, and
a trade of characters with another VMU over the link cable.

Extracted by `tools/disc-extraction/mvc2/vscom.py`. Addresses here are offsets
into the file, as the VMU's CPU sees its flash. The code runs `0x0000`–`0x272E`
and `0x5932`–`0x6D48`, the art fills `0x272E`–`0x5932`, and from `0x6D48` on are
tables the trade code reads.

**Format.** Plain 1 bit per dot, high bit first, upright, whole bytes per row,
1 = lit. Screens are built in the VMU's work RAM, 6 bytes a row, by blitters
that read d3 bytes × d4 rows with `LDC` from TRH:TRL and write at `d1+d2`,
skipping d5 bytes after each row: `0x13C1` copies, `0x1429` ORs, `0x145E` ORs
from RAM (where the number printer builds digits), `0x14BE` clears, and
`0x13F4`, whose source skips `0xDB` bytes a row, serves only the menu's scroll
transition. `0x1315` sends the 192 bytes to the LCD in order, with no turn and
no inversion; `0x12A6` sends a stored 48×32 bitmap the same way. Pointer tables
are big-endian, read through `0x14EA`.

**Language.** Many tables are indexed by the player-data byte at `0x0A4D`
(`0x2B` in RAM), clamped to 0–2: 0 picks the Japanese art, 1 and 2 the English.
Only 1 picks the copyright with ©CAPCOM U.S.A., kept as `ntsc-u`; which value the
Japanese game writes wasn't checked. The 56 fighters' names have two tables
that share most entries: 0 gives the Japanese names (TRON, BULLETA, GOUKI,
ROCKMAN, NASH, VEGA, KOBUN), 1 and 2 the overseas ones (T.BONNE, B.B.HOOD,
AKUMA, MEGAMAN, CHARLIE, M.BISON, SERVBOT), 63 name bitmaps in all.

### Screens

| Address                                                            | Archive title                                                   |
| ------------------------------------------------------------------ | --------------------------------------------------------------- |
| `0x293E` + table `0x292E` (`0x2994`–`0x2B54`)                      | Capcom logo (animation)                                         |
| `0x2C24` + `0x2B94`                                                | Title screen                                                    |
| `0x2CB4`, `0x2D74` (table `0x272E`)                                | Copyright, Copyright (Capcom U.S.A.)                            |
| `0x2E34`, `0x2EF4` (table `0x2734`) + `0x2FB4` + `0x2BC4`–`0x2BDC` | Menu (JP), Menu                                                 |
| `0x47A7`–`0x4CE7`, 8 bitmaps sent by `0x12A6`                      | Trade: connect, trading / wait, failed / error, done / finished |
| `0x5179`, `0x5239` (table `0x5173`)                                | Not enough points (JP, English)                                 |
| `0x57B2`, `0x5872`                                                 | Caution: change the battery (JP; the English one is unused)     |

- **Capcom logo.** `0x1517` clears the screen and draws the logo (`0x293E`,
  48×9) at row 4. The opening (state machine `0x1169`) shows it alone for a
  tick, then a small figure slides in from the right, 4 dots a tick (8 frames
  of 32×16 at x 16, row 16, table `0x292E`), hopping a row up or back every 4
  ticks (`0x155B`) until a 64-tick count runs out (`0x118E`). Then 64 ticks
  blank, the copyright for 192 ticks (`0x11CA`), 64 blank, and the title. The
  archive's animation is those 64 ticks; the program plays it once, the site
  loops it.
- **Title.** `0x15B3` draws `0x2C24` (48×24) and PRESS A+B (`0x2B94`, 48×8)
  under it.
- **Menu.** `0x15E9` draws the background (table `0x2734`), the item at row
  12 (table `0x273A`, 8 items, or `0x2740`, 9 once the stage list is unlocked)
  and two arrows ORed at x 16, rows 3 and 22, which the loop (`0x599D`) swaps
  every 8 ticks. The archive keeps it with item 0, LEVEL AND EXP., which the
  menu opens on (`0x1263`); the other items, and the backgrounds whole, are
  sprites. Switching items plays a 4-tick slanted wipe (`0x5A5D`, `0x5AE7`),
  not kept.
- The other screens (level, points, shop, characters, play time, net rank,
  sound) are drawn from the player's data, so only their parts are kept, as
  sprites, rather than guessing values.

**Timing.** A program step is one tick of timer 0's high byte (`0x10B1`:
t0prr `0xF5`, t0hr `0xF8`), whose interrupt (`0x0023` → `0x0052`) sets the flag
the main loop waits on (`0x10FC`). Like Power Stone Mini's, the tick is
estimated at 16 ms (about 62 Hz, counting the 32.768 kHz crystal); it wasn't
measured.

### Sprites

| Address                                     | Sprite                                                      |
| ------------------------------------------- | ----------------------------------------------------------- |
| `0x2E34`                                    | Menu backgrounds                                            |
| `0x2BC4`                                    | Menu arrows (4 × 8×8)                                       |
| `0x2FB4`                                    | Menu items (15 × 48×9, Japanese and English interleaved)    |
| `0x32DE`                                    | EXP!                                                        |
| `0x32EC` (table `0x28BE`)                   | EXP gauge, 26 steps of 32×7, indexed by exp / 4             |
| `0x35C4`                                    | LEVEL, D-Pts., N-Pts., V-Pts.                               |
| `0x366C`                                    | Character number                                            |
| `0x3714`, `0x3B5A`                          | Standby OK, Ready (and New color)                           |
| `0x37F8`, `0x3852`                          | Dreamcast play time, play time frame                        |
| `0x38A0`, `0x38CA`                          | Rank, win and lose                                          |
| `0x3906` (table `0x278A`)                   | Net ranks S–G (8 × 16×15)                                   |
| `0x39F6`                                    | Which character?                                            |
| `0x3A56`, `0x52F9`                          | Yes and no buttons, and small ones                          |
| `0x3B1C`, `0x3B2A`                          | OK?, GET!                                                   |
| `0x3BB4`, `0x3C44`                          | Sound settings, sound on and off                            |
| `0x3D04` (tables `0x27C2`, `0x2832`)        | Character names (63 × 48×7)                                 |
| `0x4761` (table `0x28A2`)                   | Digits, a font (10 × 8×7; the routines read 8 rows, draw 7) |
| `0x4DA7`                                    | Page numbers                                                |
| `0x4E25` (table `0x290E`, literal `0x5065`) | Shop price labels (7 × 48×16)                               |
| `0x50CB`                                    | Shop prompts (GETしますか?, GET?, OK?, SOLD OUT)            |
| `0x5338`                                    | NEW COLOR!, NEW STAGE!, NO. 1–7                             |
| `0x54B2` (table `0x291E`)                   | Stage list, by stages bought                                |
| `0x2974`, `0x2BE4`, `0x3780`                | Figure, menu disc, question mark (unused)                   |

Some titles ("Shop price labels", "Net ranks", "Character number") are read
from the art and where the code draws it, not from play.

**Unused.** Nothing loads these, checked against every computed TRL write
(the tables through `0x14EA`, `0x16F5`, `0x1750`, `0x2534`, and the digit
routines): the English battery caution (`0x5872`; `0x1104` shows the Japanese
one, `0x57B2`, when `P7` bit 1 is clear, before the player's data is read), the
slide's figure alone (`0x2974`, 16×16), the menu background's disc alone
(`0x2BE4`, 16×32) and a 48×20 question mark between arrows (`0x3780`). Sprites
can't be marked unused in the archive, so only this note says so.
