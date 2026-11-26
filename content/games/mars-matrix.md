# Mars Matrix

Scripts: `tools/disc-extraction/mars-matrix/`.

Dump: Redump `Mars Matrix (Japan)` (`.cue` and three `.bin` tracks; T-1238M
V1.000, 2000-09-01). The screens are in English, so none is marked as
Japan's; the American disc wasn't checked.

## What's on the disc

No file has a VMU-ish name; `/DPTEX/VMSPARTS.PVR` and `VMSPART2.PVR` belong
to the web browser the disc carries (`2_DP.BIN`), as on Guilty Gear X. The
screens are in the program itself: the boot file, `00MMXDC.BIN`, runs from
`0x8C010000` and links Sega's `pdLcd` library (version 1.04, built
1999-04-26 16:55:25, the build Grandia II and Guilty Gear X link; found by
Grandia II's bytes, at `0x8C20311C` on).

A table at `0x8C131AAC` points at six screens, back to back from
`0x8C12F3EC`. Each is 1536 bytes, a byte a dot, 8 lit and 0 not, stored as
shown:

| Entry | Screen                                     |
| ----- | ------------------------------------------ |
| 0     | The logo, MARS over MATRIX, white on black |
| 1     | LOADING                                    |
| 2     | SAVING (never shown)                       |
| 3     | SEARCHING (never shown)                    |
| 4     | OK!, in a frame of lines                   |
| 5     | NG!, in a frame of lines                   |

The save's icon follows the last screen: its palette at `0x8C1317EC`, its
picture at `0x8C13180C`. It's the one already in the archive, read from a
dumped `MARSMATRIXSV`.

## How the screens are shown

The game sends a screen with the library's write that takes a byte a dot
(`0x8C20311C`), with flag 3, after its check that a VMU with a screen is
there (`0x8C2031CC`); the library turns the screen for a VMU that reports
another orientation. The write for packed screens is linked but never
called. All of it is in one place, the memory card code at `0x8C014E80` to
`0x8C015440`, which keeps its state in a block it's handed (the number of
the screen up at `+76`, a countdown at `+80`):

- **The logo** in state 6, the rest of the time: sent once at start and
  again whenever another screen was up (`0x8C014F28`).
- **LOADING** while it works on the card (state 5; `0x8C014EE0`).
- **OK!** when an operation worked (`0x8C015406`), and **NG!** when it
  didn't (`0x8C01526E`, `0x8C015300`, `0x8C01539E`). Each sets the
  countdown, which drops by one a pass, to 20 (300 on the path at
  `0x8C0152D6`), and the logo or LOADING doesn't replace it until it runs
  out: a third of a second, or five seconds, if a pass is a 60 Hz frame.

Nothing reads entries 2 and 3, and no pointer to their art is kept
anywhere but the table, so SAVING and SEARCHING are never shown: the game
shows LOADING whatever it does with the card. None of the screens
animates.
