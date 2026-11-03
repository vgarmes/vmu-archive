# Ikaruga

Scripts: `tools/disc-extraction/ikaruga/`.

Dump: `Ikaruga v1.002 (2002)(ESP)(JP)[!]` (`.gdi`). The logo and the English
text are the same in every release, so nothing from this disc gets a region.

## What's on the disc

No file holds VMU art. Searching every file for the archive's title screen found
it in `1ST_READ.BIN`, stored upright in the archive's own encoding (1 bit per
pixel, high bit first). The rest sits right after it, from `0x8C0CFD30`; the game
runs from `0x8C010000`, so `common/find_code.py` sees its references.

| Address      | Shows                      | Archive entry                 |
| ------------ | -------------------------- | ----------------------------- |
| `0x8C0CFD30` | Title logo                 | Title screen                  |
| `0x8C0CFDF0` | SAVE                       | Save, frame 1                 |
| `0x8C0CFEB0` | SAVE, inverted             | Save, frame 2                 |
| `0x8C0CFF70` | LOAD                       | Load                          |
| `0x8C0D0030` | LOAD, bird in another pose | Load (unused)                 |
| `0x8C0D00F0` | OK                         | OK                            |
| `0x8C0D01B0` | NG                         | NG                            |
| `0x8C0D0270` | Digits 0–9, 16x16 each     | Chain counter digits (sprite) |
| `0x8C0D03B0` | CHAIN, under the digits    | Chain counter                 |

## How it's drawn

`0x8C06D0D0` steps each of two VMUs (one per controller) through a state
machine, its state at `0x8C1CB8C0` plus the VMU's number. Each state that draws
copies a screen into the VMU's buffer (`0x8C06CE88`, which turns it 180° when the
VMU is upside down) and moves to state 9, which sends it with `pdLcd`'s write
(`0x8C04B026`, called nowhere else) and waits for the send to finish.

| State | Draws                                                        |
| ----- | ------------------------------------------------------------ |
| 1     | Title screen                                                 |
| 2     | Chain counter                                                |
| 3, 4  | SAVE frame `f`, then counts to 15, flips `f` and draws again |
| 5, 6  | LOAD, then counts to 15, flips `f` and draws again           |
| 7     | OK                                                           |
| 8     | NG                                                           |

LOAD flips its frame byte just as SAVE does, but state 5 always draws the first
pose, so the second LOAD screen is never shown. It looks like the bird was meant
to hop the way SAVE blinks. It's kept, marked unused.

SAVE's timing is read from the code, not a capture: each frame is drawn, sent and
held while the counter runs to 15, at least 17 steps. The save and load loop
(`0x8C066444`) steps the VMU once per call to `0x8C011272`, which wasn't
identified; at one step per 60 Hz frame that's 283 ms a frame, the delay it was
imported with, until someone measures it.

## Chain counter

`0x8C06CF58` draws the CHAIN background, then the player's chain (the 16-bit
value at `0x8C1D13E8 + 60 + 2 * VMU`) as up to three digits over its top half:
right-aligned, hundreds at x 0, tens at x 16 and ones at x 32, all at y 0, with
leading zeros left blank. So the background alone never shows; a chain of 0
reads `0`. The digits are kept as one sprite, 0 to 9 left to right, stored as
32 bytes each (2 bytes per row). `vmu.py`'s contact sheet draws a few values the
way the game does.
