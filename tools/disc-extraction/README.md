# Disc extraction

Scripts that pull VMU screens, and the order and timing they play in, straight
from a Dreamcast disc dump. They record how each game's entries were derived, so
anyone with the same dump can check them. They are not part of the site build.

Needs Python 3.9+ and Pillow (`pip3 install pillow`). Disc dumps are never
committed; point the scripts at your own copy. Write output outside the dump's
folder, and run with `python3 -E` so nothing from the environment changes how
Python loads modules.

## Layout

- `common/` works for any game.
  - `disc.py` lists or copies files from a `.gdi` dump (the folder holding the
    `.gdi` and its tracks).
  - `sh4.py` is a small disassembler for the main CPU (SH-4), enough to read
    control flow and constants. `1ST_READ.BIN` loads at `0x8C010000`.
  - `find_code.py` finds the code that drives the VMU screen: `seq` searches for
    a known frame sequence loaded as literals, `refs` finds every caller of a
    routine.
- One folder per game, with its own README naming the exact dump it was run on.
  Code addresses only hold for that release.

## Method

1. List the disc (`disc.py <dump> inventory.json`) and look for VMU-ish names
   (`LCD`, `VMU`, `VMS`, `ICON`). Copy candidates out with `disc.py <dump> <out> <path>…`.
2. Work out the bitmap format. Try packed 1 bit per pixel (192 bytes per screen)
   and 1 byte per pixel, and both mirror directions. Berserk used bytes, mirrored.
3. Compare the decoded screens with entries already in the archive. Exact matches
   prove the decoding.
4. For order and timing, take an animation you captured from an emulator, find
   its screen numbers with `find_code.py <1ST_READ.BIN> seq …`, and read the code
   around the hit with `sh4.py`. The captured timing tells you the tick rate.
5. Write a per-game script that walks that code and emits every animation, then
   import the result with `pnpm icons:import`.

Captures stay the ground truth: a game's code says what it can play, a capture
shows what it did.

## Games

| Game | Dump | Folder |
| --- | --- | --- |
| Sword of the Berserk: Guts' Rage | US v1.000 (2000, Eidos) | [`berserk/`](berserk/) |
| Bakuretsu Muteki Bangaioh | JP v1.003 (1999, ESP) | [`bangaioh/`](bangaioh/) |
| Moero! Justice Gakuen | JP v1.004 (2000, Capcom) | [`justice/`](justice/) |
| Power Stone, Power Stone 2 | JP v1.020 (1999), JP v2.000 (2000), Capcom | [`power-stone/`](power-stone/) |
| Shenmue II | JP v1.003 disc 1 (2001, Sega) | [`shenmue2/`](shenmue2/) |
