# Metropolis Street Racer

Scripts: `tools/disc-extraction/msr/`.

Dump: `MSR - Metropolis Street Racer (Europe) (En,Fr,De,Es) (Rev B)` (Redump,
`.cue`). The screens have no text in any one language and carry the MSR logo
every release uses, so they get no region.

## What's on the disc

No file holds the VMU screens. The `IMAGES/*.TGA` files (`SINGL`, `MULTI`,
`GHOST`, `CHALL`, `ICON`, compressed, starting `Pak`) are the colour icons of
the memory card files, which the program checks for size and colours
("Wrong Icon Size", "Too many colours in icon"), and `BROWSER/DPETC/VMS.DPS`
belongs to the bundled Dream Passport browser.

The game itself is `MSR.BIN`; `1ST_READ.BIN` only loads it. It runs from
`0x8C010000` (where 2,221 of its string pointers agree), and the screens sit
there back to back, 192 bytes each:

| Screen           | Address      | Archive entry |
| ---------------- | ------------ | ------------- |
| MSR, the Kudos K | `0x8C10C9F0` | Title screen  |
| MSR, OK!         | `0x8C10CAB0` | OK!           |
| MSR, SAVING..... | `0x8C10CB70` | Saving        |

The screens were found by scanning `MSR.BIN` for 192-byte blocks whose rows
look like their neighbours; the code's pointers set where each begins, 4 rows
above the logo.

Every screen goes through `0x8C02F224` (a mask of ports, the screen, a flag).
It spreads bit `i` of the screen, read low bit first (byte `i >> 3`, bit
`i & 7`), to a byte of `0xFF` or `0` in a 1,536-byte buffer, row by row, then
sends that buffer to each port in the mask through the library's LCD write
(`0x8C11D4C4`). A 1 is lit and nothing turns or inverts the screen, so it's
stored the way up the VMU shows it; only each byte's dots run from its low
bit, the reverse of most games.

- **Title screen.** Sent to all four ports at boot (`0x8C010418`). It's the
  screen the VMU goes back to.
- **Saving.** Sent as a save starts (`0x8C06EFD4`).
- **OK!** Sent by `0x8C02F3AE`, called from `0x8C06EC5C`; going by what it
  shows, that runs when a save finishes. It also sets that slot's countdown (`0x8C10C7A4`) to 150.
  The VMU code's per-frame update (`0x8C02EF08`) counts it down for each of
  the 8 slots and puts the title screen back when it reaches 0. At 50 Hz
  that's 3 seconds, at 60 Hz 2.5; which rate the game runs at wasn't traced.

Nothing animates.

## The font

The VMU code also has a `printf` for the VMU (`0x8C02EB00`): it formats a
string, maps each character through a 256-byte table (`0x8C10C7AC`) to one
of 38 glyphs (`0x8C10C8AC`), and draws them in lines 8 dots apart, wrapping
at 48 dots. Nothing calls it, so the game never shows the font; it's
kept as a sprite, tagged `unused`.

A glyph is 8 bytes, a row each; a row's top 5 bits are its dots. Row 0's low
3 bits are the glyph's advance, and the renderer draws one column fewer, the
last being the gap. The table maps space and unknown characters to glyph 0
(blank, advance 1), A–Z and a–z to glyphs 1–26, 0–9 to 27–36, and `0x0A` to
glyph 37, a newline: it moves the pen down and draws nothing. The sprite
keeps glyphs 0–36, 5 dots wide, with each advance as its width; the
newline's 8 empty bytes are left out. `vmu.py` rebuilds the 304 bytes from
the sprite and checks them against the disc.

## Save icons

Not checked against this disc: the icons in `IMAGES/` are compressed, and the
decompressor wasn't traced. The archive's two come from dumped saves.
