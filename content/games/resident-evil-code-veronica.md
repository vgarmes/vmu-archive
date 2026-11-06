# Resident Evil Code: Veronica

Scripts: `tools/disc-extraction/cvx/`.

Dumps: `Biohazard - Code - Veronica (Japan) (Disc 1)` and `Resident Evil -
Code - Veronica (Europe) (Disc 1)` (Redump, `.cue`). The addresses below are
the Japanese program's.

## Japan and Europe

The only difference on the VMU is the title. Japan's says BIOHAZARD, so it's
kept as `ntsc-j`; Europe's says RESIDENT EVIL over the same CODE: Veronica.
The American disc wasn't checked; it very likely has the European title too,
so that title gets no region rather than `pal`. Every other screen is the same
in both and gets no region.

The European `1ST_READ.BIN` holds the sheet at `0x8C1404B8`. It differs from
the Japanese one only in rows 7–14, the BIOHAZARD band. The rectangle table
and everything after the sheet are the same, apart from pointers. So is the VMU
code, 0x2D5C bytes later, instruction for instruction except for the pointers
it loads, and the trace lists, at `0x8C1705C0`. The three save icons are the
same bytes, 0x35AC bytes later. Only the names on the card change:
`RECV%02u_GAMEDATA`, with descriptions `RE_CV/CLAIRE/`, `RE_CV/CHRIS/`,
`RE_CV/DUMMY/` (Japan's `BIO_CV/ｵﾏｹ/`) and `RE_CV/SYSTEMDATA`.

## What's on the disc

No file holds the VMU art. It's one 128x128 1-bit sheet in `1ST_READ.BIN`,
which runs from `0x8C010000`, at `0x8C13CEFC`: 16 bytes a row, bit 7 leftmost,
a set bit lit, stored as shown. A table of 56 rectangles follows it at
`0x8C13D6FC`, each four 16-bit values: y, x, height, width. They tile the
sheet exactly, every dot in one rectangle, and every rectangle appears whole
on one of the screens here, so the screens keep everything the sheet holds and
there are no separate sprites.

| Rects | What                                                    |
| ----- | ------------------------------------------------------- |
| 0     | The title screen, BIOHAZARD / CODE: Veronica, 48x32     |
| 1–4   | SAVE, LOAD, OK, NG                                      |
| 5     | CAPCOM                                                  |
| 6–10  | FINE, CAUTION, DANGER, DIED, POISON                     |
| 11    | The monitor's sweep column, 8x24                        |
| 12–47 | Six heartbeat traces, each cut into six 8-pixel columns |
| 48–50 | YOU DIED, three stages of dripping                      |
| 51    | Mission Clear!                                          |
| 52–55 | 32x32 portraits: Claire, Chris, Steve, Wesker           |

## How the screens are drawn

Each screen is composed on a 64x64 canvas, of which the VMU shows the top-left
48x32. `0x8C12D054` copies a rectangle of the sheet onto it (whole bytes, so
everything sits on 8-pixel columns) and `0x8C12D1AC` fills part of it, clear
or lit. `0x8C12CF68` sends the 48x32 as stored, or turned 180° for a VMU
that reports the other orientation.

A small interpreter runs the VMU (`0x8C12CE3C`), from byte programs: `0`
waits a tick, `1 n` waits `n`, `2 m` switches to draw mode `m`, `3 n` picks
the VMU to draw on, `FF` ends. Draw modes are a table of (routine, argument)
pairs at `0x8C13D8BC`:

| Mode  | Routine      | Draws                                                |
| ----- | ------------ | ---------------------------------------------------- |
| 1, 2  | `0x8C12D23C` | CAPCOM at y 12 on a clear screen                     |
| 3     | `0x8C12D290` | The title screen                                     |
| 4–7   | `0x8C12D2AA` | SAVE, LOAD, OK, NG at y 9 on a lit screen            |
| 8     | `0x8C12D2E8` | A clear screen                                       |
| 9     | `0x8C12D304` | The condition monitor                                |
| 10    | `0x8C12D444` | YOU DIED                                             |
| 11    | `0x8C12D4E6` | Mission Clear! at y 12                               |
| 12–16 | `0x8C12D50C` | A portrait at x 8; mode 15 picks it by the character |

The memory card code asks for modes through `0x8C12CC58` (blank and SAVE
directly, the rest from tables), and `0x8C12CD60` switches modes when bits
of a game event mask change, through the table at `0x8C13D95C`. Mode 15 reads
the same character byte the save code does (see Save icons): Claire's,
Chris's, then Steve's for the bonus mode, from the table at `0x8C13DA58`.

**The condition monitor.** Mode 9 reads the player at `[0x8C13E19C]` and picks
one of six statuses: DIED if its dead flag is set, POISON if it's poisoned
(`0x280000` at `+0x88`), else by health (`+0x41C`): FINE from 120, CAUTION
from 60, CAUTION again from 30 with a weaker beat, DANGER below. Each has its
label (`0x8C13DA50`), its trace (`0x8C16D488`) and the row to draw it at
(`0x8C13DA38`). It draws the label at the bottom, then sweeps the sweep
column across the screen one column every 2 ticks, erasing the old trace;
from the sweep's fifth column it redraws the trace a column a tick behind it,
holds 12 ticks, and starts again. The status is read again every sweep. The
archive keeps one sweep as it repeats, starting from the full trace.

**YOU DIED.** Mode 10 lights the whole screen and counts down 42 ticks
(45 before the first stage shows, with the steps between states), then draws
the three stages 16 ticks apart (18 ticks a stage, likewise) and stays on the
last. The site loops, so the last is held 3 s.

**Timing.** The VMU code (`0x8C12CBF6`) runs on every second pass of the game
loop that calls it (`0x8C12EA62`). That loop is taken to run at 60 Hz, so a
tick is 1/30 s; what paces the loop wasn't traced.

## Save icons

The three icons the game writes sit back to back in `1ST_READ.BIN`, each a
palette then its frames, as the save header takes them. All three match the
archive's entries byte for byte, though those came from dumped saves (two
Japanese, one American):

| Icon                  | Address      | Frames, speed | Loaded at    | Archive entry |
| --------------------- | ------------ | ------------- | ------------ | ------------- |
| Zombie face           | `0x8C13BC20` | 1, 30         | `0x8C12BE64` | System file   |
| CODE: Veronica, red   | `0x8C13BE40` | 3, 30         | `0x8C128BA0` | Claire's save |
| CODE: Veronica, olive | `0x8C13C460` | 3, 30         | `0x8C128BAA` | Chris's save  |

The system file is `VERONICA.SYS`, with the description `BIO_CV/ｼｽﾃﾑﾃﾞｰﾀ`
(system data). A game save is `VERONICA.%03u`, named `BIO_%02u_GAMEDATA`, its
description built from the character, the difficulty (`N/`, `E/`, `V/`) and
the room. The builder at `0x8C128ACA` reads the character from byte `+0x84`
of the game state: 0 writes `BIO_CV/ｸﾚｱ/` (Claire), 1 `BIO_CV/ｸﾘｽ/` (Chris),
2 `BIO_CV/ｵﾏｹ/` (bonus). The same byte picks the icon: Claire's saves get the
red one, every other save the olive one. The saves the archive's entries came
from agree: the red one is from a `BIO_CV/ｸﾚｱ/…` save, the olive one from an
American `RE_CV/CHRIS/…` save. The Japanese program holds both, so neither is
region-only.

The program also has a routine that writes a memory card icon,
`ICONDATA_VMS` (`0x8C12C910`), but nothing calls it.
