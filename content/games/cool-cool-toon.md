# Cool Cool Toon

Scripts: `tools/disc-extraction/cool-cool-toon/`.

Dump: Redump `Cool Cool Toon (Japan)` (`.cue` and three `.bin` tracks;
T-3106M V1.012, 2000-06-12). The game was only released in Japan, so its
pieces are `ntsc-j`.

## What's on the disc

`1ST_READ.BIN` runs from `0x8C010000` and links Sega's `pdLcd` library
(version 1.04). The files in `/CCT` with VMU-ish names aren't screens:
`VMS.MNI` is a 3D model and `VMSPR.HBN` on-screen sprites, both for the
game's own VMU menu on the TV. `VM_ICON_*.HBN` are the save icons (below).

### Screens

Six screens, 192 bytes each from `0x8C09F3B8`, packed 1 bit a dot (high bit
leftmost) and upright; their pointers follow at `0x8C09F838`. `0x8C0596BC`
sends screen k to one player's VMU and `0x8C0596EE` to all eight slots, both
through `0x8C054E30`, which turns the screen 180° for a VMU that needs it
(`0x8C21EC20` says which) before pdLcd's write for packed screens.

| Screen | Shows         | Archive entry       |
| ------ | ------------- | ------------------- |
| 0      | nothing       | not kept: blank     |
| 1      | STORY         | Story               |
| 2      | COOLCOOL TOON | Cool Cool Toon logo |
| 3      | SAVE          | Save                |
| 4      | NOTTY         | Notty               |
| 5      | FLITZ         | Flitz               |

Screen 3 is shown on a player's VMU right after `COOLCOOL.SYS` is written
(`0x8C057FC4`), and screen 0 after another write of it (`0x8C0575CC`). The
others go to every VMU from `0x8C01916C`, which takes the screen from the
game's mode logic (a parameter, or a table at `0x8C3636F4`); which mode
shows which screen wasn't traced. A VMU plugged in later gets the current
screen again (`0x8C01A9C8`).

## Save icons

`COOLCOOL.SYS`'s icon is one of four files, `/CCT/VM_ICON_BOY.HBN`, `_GIRL`,
`_MAN` and `_WOMAN`, each a character's portrait winking over three frames. Each is an `MBIN` file (version 4) of four
sections: the three frames (512 bytes each, 4 bits a dot) and the palette
(32 bytes), each packed with LZSS: a flag byte read low bit first (1 a
literal); a reference is 12 bits of window position and 4 of length − 3,
in a zeroed 4 KiB window written from `0xFEE`. The program loads all four
(`0x8C056820`).

- **Confirmed.** The icon already in the archive, read from a dumped save, is
  `VM_ICON_MAN.HBN`: all three frames and the palette match it byte for byte.
  It's now titled System file (man).
- **Added.** The boy, girl and woman icons, rebuilt from their files, with
  the dumped save's speed (10) and names (ｸﾙｸﾙﾄｩｰﾝｼｽﾃﾑ, クルクルトゥーン).
  Where the game copies an icon into the save wasn't traced, so that it picks
  the icon by the chosen character is inferred, not shown.

The game also reads a `COOLCOOL.DWN`.
