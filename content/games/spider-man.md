# Spider-Man

Scripts: `tools/disc-extraction/spider-man/`.

Dump: Redump `Spider-Man (USA)` (`.cue` and five `.bin` tracks). Nothing
here is marked as one region's: the European disc wasn't checked.

## What's on the disc

`1ST_READ.BIN` runs from `0x8C010000` and links Sega's `pdLcd` library
(version 1.04). The VMU art is in five files of their own, named for what
they show:

| File            | Screen                                             |
| --------------- | -------------------------------------------------- |
| `VMULOGO.BMP`   | Spider-Man's mask, the screen the VMU rests on     |
| `VMUSAVE.BMP`   | A VMU with an arrow going into it, and _Saving..._ |
| `VMULOAD.BMP`   | A VMU with an arrow leaving it, and _Loading..._   |
| `VMUOK.BMP`     | The VMU and a ringed OK, and _O.K._                |
| `VMUFAILED.BMP` | The VMU and a ringed !, and _Failed!_              |

Each is a Windows BMP, 48x32 at 8 bits a dot with a two-colour palette
(white, then black), 1600 bytes. The black dots are the lit ones.

## How the screens are shown

`0x8C191580` loads a BMP into a picture: a width byte, a height byte, then a
byte a dot in rows padded to 4. `0x8C191D80` copies one into a 48x32 buffer
(`0x8C337950`) and sends it with the library's write (`0x8C044F74`), which
takes a byte a dot, non-zero lit, turning it for a VMU that reports another
orientation. If a file won't load it draws a stand-in instead, a 4x4
checker of 8s at `0x8C1C6358`, in the top left corner. That isn't kept as a
sprite: the game draws it only when its art is missing.

- **The mask.** `0x8C191F80` loads `VMULOGO.BMP` once and sends it to every
  VMU the library knows of; `0x8C192320` loads it without sending. It's what
  the VMU shows whenever nothing else is. The game has no VMU title screen,
  so the mask is its card's cover.
- **Saving.** The save routine (`0x8C18F800`) shows `VMUSAVE.BMP` first,
  then `VMUOK.BMP` (`0x8C18FB28`) or `VMUFAILED.BMP` (`0x8C18FBCA`).
- **Loading.** The load routine shows `VMULOAD.BMP` (`0x8C18FC40`), then
  `VMUOK.BMP` (`0x8C18FD06`) or `VMUFAILED.BMP` (`0x8C18FD42`).

None of them animates. After OK the game calls `0x8C190720` with 30: it
starts the VMU's buzzer and lowers its pitch each tick for 15 ticks, a
falling beep, when the game's VMU Beep option is on. The screen stays until
the next one replaces it.

## Save icons

The save icon already in the archive, read from a dumped `SPIDRMAN.DAT`,
isn't stored plainly in `1ST_READ.BIN`; it wasn't looked for in the data
files.
