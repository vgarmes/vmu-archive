# Sakura Taisen 3: Paris wa Moete Iru ka

Scripts: `tools/disc-extraction/sakura3/`.

Dump: `Sakura Taisen 3 - Paris wa Moete Iru Ka v1.003 (2001)(Sega)(JP)(Disc 1 of 3)[!][3M1]`
(`.gdi`). Every entry from it has region `JP`.

**Partly imported.** 26 stills, the animated title screen and 23 scrolling
battle banners are in the archive; the other animations and the strategy map wait (see [Waiting](#waiting)).

## What's on the disc

VMU art is stored in `LCD1` blocks: standalone `.LC1` files, and blocks inside
the minigame executables, the strategy maps (`SLG/G0x/SMAP0x.ESM`) and the battle
units (`SLG/UNITS/*.BC`). The format is in `vmu.py`. `1ST_READ.BIN` loads at
`0x8C010000`; the loader is at `0x8C15EC3C` and the nibble run-length decoder at
`0x8C15ECC0`.

An entry unpacks to one byte per pixel, a brightness from 0 (dark) to 15
(light). The game composes the VMU screen at that depth (its text routine at
`0x8C12331C` blends glyphs in brightness) and converts to 1 bit when it sends it;
that conversion wasn't found in the code. A Flycast capture of the logo (entry 4,
frame 10) settles it: a dot is lit where the value is below 8. That frame
matches the capture in all but 81 of 1,536 dots (edges of a 3.7x scaled
capture), and 181 of its 193 dots of value 7 show lit. Value 8 (64 dots in
`SYSTEM.LC1` entry 3) isn't covered by a capture yet, so `prep.py` refuses it.

| Source                           | Entries   | Content                                                                                                                          |
| -------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `ADVDATA/SYSTEM.LC1`             | 5         | power-on animation (6 frames), crest, Message, crest with grey, サクラ大戦3 logo intro (11 frames)                               |
| `MINIGAME/KAJINO1`–`3.LC1`       | 10 each   | カジノ大戦 intro, one step per entry                                                                                             |
| `MINIGAME/MG*.BIN`, `MGKG_*.LC1` | 8 each    | a character's face, 4 expressions, each with an eyes-closed (blink) frame                                                        |
| `SLG/G01`–`G06/SMAP0x.ESM`       | 3 each    | two empty map frames, and a 96×48 sheet of parts (DESTROY, TARGET, HP, MP, digits) the game draws enemy positions and stats with |
| `SLG/UNITS/*.BC`                 | 1–11 each | banners wider than the screen (128–400 px): attack names, scrolled 1 px per 60 Hz tick                                           |

## Imported

| Entries                                                                | Archive title                                                                      |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `system-01`                                                            | Crest                                                                              |
| `system-02`                                                            | Message                                                                            |
| `system-04`, all 11 frames                                             | Title screen (animated, 100 ms a frame, logo held 4 s)                             |
| `mgkg_coq`, `_eri`, `_gly`, `_han`, `_oga`, `_rob`: entries 0, 2, 4, 6 | Coquelicot, Erica, Glycine, Hanabi, Ogami, Lobelia (4 expressions each, eyes open) |

**Title screen.** A Flycast recording of the logo intro plays `system-04`
frames 0–10 in order: blank, a line that opens to a lit screen, the logo
unfolding from it. The frame changes average 104 ms over the nine steps
(capture jitter 50–150 ms), so each frame is taken as 100 ms (6 ticks). The
logo then stays up about 4.2 s before the map; the entry holds it 4 s before
looping.

The `MG*.BIN` minigames carry the same faces as the `MGKG_*` files (Ogami's in six
of them), so they add nothing.

**Banners.** 23 unique strips (the 13 unit files hold 53; a heroine's second
and third banners are repeated in Ogami's three files, as attacks together, and
carry both characters' tags). They import as scroll entries with `stepPx: 1`
and `delayMs: 17`: a Flycast recording of Gigantesque ciseau shows the strip
entering from the right and leaving past the left at 59.6 px/s, 1 px per 60 Hz
tick (fit within 1.6 px median). The other banners are assumed to scroll the
same way; one routine plays them all. Titles keep the art's spelling (no
accents); the Japanese ones add their reading, so their ids are readable.

## Waiting

Things to check in an emulator (Flycast) before importing the rest:

1. **Flicker.** One capture can't rule out the game alternating grey dots; a
   second capture of the same screen with the same dots lit would.
2. **Value 8.** Capture the second crest (`SYSTEM.LC1` entry 3).
3. **Timing.** The power-on animation, the カジノ大戦 intros and
   the faces' blinks; capture them playing for frame order and timing.
4. **Maps.** The map frames alternate (about 267 / 67 ms in a recording) with
   units drawn on top at run time; left out for now.
5. **Banner speed.** Only Gigantesque ciseau was measured; a capture of another
   banner would confirm they all scroll at 1 px per tick.
6. **Battle screen.** A recording shows a battle VMU screen (DESTROY 5, HP / MP
   swapping with their values, 1 TARGET) that no LCD1 block on the disc holds
   (all 1,261 files scanned), and its rows, rebuilt from the recording, aren't
   in any file as raw 1-bit data either. Its numbers change, so the game likely
   draws it at run time from parts; left out for now. Finding them means
   tracing the battle code in `1ST_READ.BIN`, or a sharper capture to search
   with.
