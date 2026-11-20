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
32 rows of 6 bytes, into a VMU's buffer. For screens 0–4 it then calls the
matrix routines at `0x8C109F50` on with an angle and scale kept at
`0x8C17F7DC`–`0x8C17F7E8`, so those can be drawn turned and scaled; the
rotation itself wasn't traced, and only the stored screens are kept.

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
