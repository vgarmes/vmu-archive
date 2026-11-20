# Virtua Tennis 2

Scripts: `tools/disc-extraction/vt2/`.

Dump: Redump `Virtua Tennis 2 - Sega Professional Tennis (Europe)
(En,Ja,Fr,De,Es)` (`.cue` and three `.bin` tracks). The game was released as
Power Smash 2 in Japan and Tennis 2K2 in the US, and this disc carries all
three titles' VMU logos.

## What's on the disc

No file holds the VMU screens (the `SPRITE_*_VM_*.BIN` files are colour
textures, one set per title). Eleven screens sit back to back in
`1ST_READ.BIN`, which runs from `0x8C010000`, from `0x8C17EF8C` on: 1 bit a
dot, high bit first, turned 180° as the LCD takes them (as in Crazy Taxi 2 and
Jet Set Radio).

| Index | Address      | Screen          | Archive entry                | Region   |
| ----- | ------------ | --------------- | ---------------------------- | -------- |
| 0     | `0x8C17EF8C` | Power Smash 2   | Title screen (Power Smash 2) | `ntsc-j` |
| 1     | `0x8C17F04C` | Virtua Tennis 2 | Title screen                 | `pal`    |
| 2     | `0x8C17F10C` | Tennis 2K2      | Title screen (Tennis 2K2)    | `ntsc-u` |
| 3     | `0x8C17F1CC` | OK!             | OK                           |          |
| 4     | `0x8C17F28C` | NG!             | NG                           |          |
| 5–8   | `0x8C17F34C` | 1P to 4P        | 1P, 2P, 3P, 4P               |          |
| 9     | `0x8C17F64C` | Now Loading...  | Now Loading                  |          |
| 10    | `0x8C17F70C` | Now Saving...   | Now Saving                   |          |

Only the block's base is in the code: `0x8C033CFE` copies screen `r5` from it,
32 rows of 6 bytes, into a VMU's buffer. The VMU code runs every second frame
of the game loop (`0x8C032F74`), so a step is 33 ms if the loop runs at 60 Hz.

## The turning title

The logo turns into place when the VMUs are set up. Nothing of the turn is
stored: for screens 0–4, while a depth kept at `0x8C17F7DC` is below 1, each
step redraws the screen in 3D from its own dots (`0x8C033D74`). The archive's
three turning titles are redrawn by `turn.py`, which re-runs that renderer in
single-precision floats.

- **Motion** (`0x8C033486`). The setup (`0x8C0331D0`) starts the depth z at
  −0.1 and the tilt (`0x8C17F7E0`, a 16-bit angle) at −90°. Each step, while
  the tilt is negative, z falls by 1/15 and the tilt rises by 546.13; then,
  while z is below −1, z rises by 1/60 and the spin (`0x8C17F7E4`) by 955.73.
  The angles are added as floats and truncated back to 16 bits. When neither
  applies, z is set to 1 and the plain screen shows. That's 97 drawn steps,
  the plain logo the 98th.
- **Matrix** (`0x8C033D7E`). The library's matrix starts as the identity, is
  translated by (0, 0, z) and rotated about Y by `0x8C17F7E2` (always 0),
  about X by the tilt (`0x8C10A090`) and about Z by the spin (`0x8C10A300`),
  each multiplied on the right with FTRV.
- **Dots** (`0x8C033EFC`). For each lit dot (x, y) of the logo the renderer
  makes a point ((x − 24)/sx, (16 − y)/sy, 0), with sx = 24/tan 15° and
  sy = 16/tan 10° (a field of view of 20 out of 90, scaled by 3π/8 and π/4).
  `0x8C033EA4` gives the point a z of 1, but `0x8C034044` overwrites it with
  0, so the logo's plane passes through the eye and z alone sets its depth.
  The point is turned by the matrix's 3×3 part, the translation added, and
  projected at 24 + x·sx/|z|, 16 − y·sy/|z| (a point behind the eye is drawn
  as if in front), truncated, and set if it lands on the screen.

So the logo swings down from above, edge on, recedes to half size as it
faces the player, then spins almost a full turn as it comes back to full size.
The game plays it once; the site loops it. The code turns whichever logo the
release global picked, so each release's logo gets the same turn.

`0x8C03327A`, which shows a screen for 120 steps, replays the turn after its
count runs out, from z = 0 instead of −0.1; that variant isn't kept.

**Which title.** When the VMUs are set up (`0x8C03317A`), each one's title is
picked by a global at `0x8C2C9EE4`: 0 gives screen 0, 1 gives screen 2, any
other value screen 1. The same global is read in some 30 places. This
European program sets it to 2 at start (`0x8C010D4A`) and nothing else writes
it, so it shows only the Virtua Tennis 2 logo; 0 and 1 are the Japanese and US
releases, whose titles the other two logos carry. Hence the regions.

## Save icon

One icon serves every release: its palette at `0x8C240E80` and frame at
`0x8C240EA0`. The names before it come in one set per release, through a
pointer table at `0x8C240D84` (what indexes it wasn't traced):

| Release | Memory card name | VMU name        | Description        |
| ------- | ---------------- | --------------- | ------------------ |
| Japan   | `POWER_SMASH2`   | ﾊﾟﾜｰｽﾏｯｼｭ2 ﾃﾞｰﾀ | パワースマッシュ２ |
| US      | `TENNIS_2K2__`   | `TENNIS2K2_DAT` | `TENNIS2K2`        |
| Europe  | `V_TENNIS2___`   | `VIRTUATENNIS2` | `VIRTUATENNIS2`    |

- **Confirmed.** The save icon already in the archive, read from a dumped US
  save (`TENNIS_2K2__`), is the game's own: its palette and frame match the
  disc's byte for byte.
