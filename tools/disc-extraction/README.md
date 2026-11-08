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
  - `disc.py` lists or copies files from a dump: the folder holding a `.gdi`
    or a Redump `.cue`, and its tracks.
  - `sh4.py` is a small disassembler for the main CPU (SH-4), enough to read
    control flow and constants. `1ST_READ.BIN` loads at `0x8C010000`.
  - `lc86k.py` is the same for the VMU's own CPU (LC86K), for VMU programs a
    game carries. `refs` finds where the code loads an address into TRH/TRL,
    the pointer its `LDC` reads art through.
  - `find_code.py` finds the code that drives the VMU screen: `seq` searches for
    a known frame sequence loaded as literals, `refs` finds every caller of a
    routine.
- One folder per game, with its own README naming the exact dump it was run on
  and how to run its scripts. Code addresses only hold for that release.
- What the scripts found is not here: each game's notes are in
  `content/games/<game slug>.md` (the slug of the archive's `game` name, as in
  `content/sprites/`), so the site can show them.

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
6. Smaller art the game draws onto a screen (digits, buttons, counters) isn't a
   screen, but keep it: have the script emit it with `"sprite": true` in its
   sidecar, and the importer stores it at its own size in `content/sprites/`.
   The site never shows sprites; `pnpm content:check` validates them.
   Keep a font in the archive's one form, whatever the disc's layout: one
   sprite, upright, its characters one under the next in the game's order,
   with each character's size in `"glyphs"` (see `src/lib/glyphs.ts`). Never
   lay pieces out in a grid or side by side. Keep every stored pixel, dropping
   only bytes shown to be empty padding, and have the script rebuild the
   disc's bytes from what it keeps and compare them (Jet Set Radio's `app.py`,
   with per-glyph headers, and the VMU BIOS's `vmubios.py`, with planes, do).
7. Write the findings (format, timing, unused screens, sprites) in the game's
   notes, `content/games/<game slug>.md`, one file per game in the archive. The
   game's README here keeps the dump and how to run its scripts, and links to
   the notes.

Captures stay the ground truth: a game's code says what it can play, a capture
shows what it did.

## How games store their VMU art

Every game so far did it differently. What has turned up:

**Where it lives.**

- In the program itself, `1ST_READ.BIN`, with no file of its own: Bangaioh,
  Crazy Taxi 2, Ikaruga, Jet Set Radio, Marvel vs. Capcom 2, Moero! Justice
  Gakuen, Power Stone 1 and 2, Resident Evil Code: Veronica, Sonic Shuffle,
  Street Fighter III 3rd Strike.
- In the game's own program, loaded by a small `1ST_READ.BIN`: Metropolis
  Street Racer's `MSR.BIN` (it runs from `0x8C010000`; string pointers give
  the base away).
- In a Windows CE program's `.data`: Shinseiki Evangelion: Typing E-Keikaku's
  `TYPE_E.EXE` (a PE file; map addresses through its section table).
- In a dedicated file: Berserk's `LCDIMG.BIN`.
- In a VMU program the game carries for the VMU to run, with its own code:
  Shenmue Passport's Goodies viewer (`SYEN.BIN`), Power Stone Mini, a whole
  VMS image inside Power Stone's `1ST_READ.BIN`, and Jet Set Radio's graffiti
  viewer, the first member of `JETRADIO/SYSOPTION.AFS`, and Marvel vs.
  Capcom 2's VS.COM, `/VS4.BIN`, which the game writes to the memory card. Find one by its VMS header
  (a 16-byte description at `+0x200`); read its code with `lc86k.py`.
- In a system ROM, not a disc: the VMU's own BIOS (fonts and clock sprites,
  from which it builds every screen) and the Dreamcast's `dc_boot.bin` (its
  memory card icons). See [`bios/`](bios/).
- As a chunk inside a bigger file: Shenmue and Shenmue II's `IWAD` chunk in
  `MISC/COLD.BIN`.
- As small blocks in many files: Sakura Taisen 3's `LCD1` blocks, in its own
  `.LC1` files and inside minigame and battle files.
- Inside an archive, per character: Soul Calibur's `HUMAN.DAT`.

File names rarely help. Shenmue II's `SPRITE/VM_*.GZ` sound like VMU art but are
colour textures; the real art was found by following the code that loads it.

**How the dots are stored.**

| Encoding                 | Example                                                                                   |
| ------------------------ | ----------------------------------------------------------------------------------------- |
| 1 bit per dot, as shown  | Moero! Justice Gakuen, Ikaruga, Shenmue 1 and 2 (with a width and height byte)            |
| 1 bit per dot, low first | Metropolis Street Racer: bit 0 of each byte is the leftmost dot                           |
| 1 bit per dot, a sheet   | Code: Veronica: one 128x128 sheet, cut by a rectangle table into every screen's parts     |
| 1 bit per dot, rotated   | Bangaioh, Crazy Taxi 2, Jet Set Radio, Typing E-Keikaku: turned 180°, as the LCD takes it |
| 1 bit per dot, inverted  | Power Stone's title (the game inverts it again before sending)                            |
| 1 bit per dot, masked    | Power Stone Mini: each row is the mask's bytes, then the image's                          |
| 1 byte per dot, mirrored | Berserk                                                                                   |
| 1 byte per dot, a sheet  | Sonic Shuffle's hand: one 48x32 sheet of 8 (lit) or 0, cut by a rectangle table           |
| Brightness 0–15 per dot  | Sakura Taisen 3: lit where the value is below 8                                           |
| Several values per dot   | Soul Calibur: 15 lit; 0 and 128 unlit (figure and background)                             |

So try every packing, every flip and mirror, and inverted bits before
concluding the art isn't there. A sprite can also be stored eight times, shifted
right 0–7 dots so the VMU never shifts at run time (Power Stone Mini); copy 0
is the art.

**Compression.** Most games store their art plainly, which is why searching the
disc for an entry already in the archive usually works. Two don't:

- Sakura Taisen 3 run-length codes its `LCD1` blocks (one byte: a 4-bit run and a
  4-bit value).
- Soul Calibur packs its pictures with the game's own LZ routine
  (`0x8C0EE76C`), used for much of the game's data. No plain search or common
  decompressor (LZSS, PRS) finds them; reimplementing that routine does.

If a known screen doesn't turn up anywhere, look for the decompressor: a
short loop that reads a flag byte bit by bit, copies literal bytes, and copies
runs from earlier in its own output. Then run it on each member of the data
files and look for the screen in what comes out.

**Order and timing.**

- From code tables: Berserk (frames held 4 or 8 ticks of 60 Hz), Bangaioh
  (animation scripts) and Crazy Taxi 2 (a frame counter, assuming a 60 Hz
  loop). Ikaruga's SAVE holds each frame while a counter runs to 15, which
  gives at least 17 steps, but what paces a step wasn't traced. Power Stone
  Mini's Falcon course: the order of its sections and the speed from code, the
  tick estimated from a timer's setup. It scrolls down the screen, so it's a
  `"direction": "down"` scroll (see the main README). Jet Set Radio's radio:
  a null-terminated list of screens stepped every 6 ticks, assuming 60 Hz.
- Rebuilt from drawing code: Jet Set Radio's graffiti viewer composes its
  screens from bitmaps, sprites and font strings, so they were redrawn from
  what its code places where. Its ticks come from the VMU's base timer at a
  rate it never sets, so they play at the site's default. Code: Veronica
  composes every screen from its sheet with a small byte-code interpreter and
  draw modes, so its screens were redrawn by re-running those modes tick by
  tick (a tick every second pass of the game loop, assuming 60 Hz).
- From captures: Sakura Taisen 3's title (100 ms a frame) and its scrolling
  banners (1 px per tick, stored as one strip; see the main README).
- Unknown yet: Soul Calibur's fighters play at the site's default until someone
  captures them.

The code also says what the game never shows: screens nothing calls are marked
`unused` (Berserk, Bangaioh, Ikaruga's second LOAD pose).

## Games

| Game                             | Dump                                        | Folder                             | Notes                                                                                                                     |
| -------------------------------- | ------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Sword of the Berserk: Guts' Rage | US v1.000 (2000, Eidos)                     | [`berserk/`](berserk/)             | [berserk-millennium-falcon-hen-wasurebana-no-sho](../../content/games/berserk-millennium-falcon-hen-wasurebana-no-sho.md) |
| Bakuretsu Muteki Bangaioh        | JP v1.003 (1999, ESP)                       | [`bangaioh/`](bangaioh/)           | [bangai-o](../../content/games/bangai-o.md)                                                                               |
| Moero! Justice Gakuen            | JP v1.004 (2000, Capcom)                    | [`justice/`](justice/)             | [project-justice](../../content/games/project-justice.md)                                                                 |
| Power Stone, Power Stone 2       | JP v1.020 (1999), JP v2.000 (2000), Capcom  | [`power-stone/`](power-stone/)     | [power-stone](../../content/games/power-stone.md), [power-stone-2](../../content/games/power-stone-2.md)                  |
| Shenmue                          | JP v1.007 disc 1 (1999, Sega)               | [`shenmue/`](shenmue/)             | [shenmue](../../content/games/shenmue.md)                                                                                 |
| Shenmue II                       | JP v1.003 disc 1 (2001, Sega)               | [`shenmue2/`](shenmue2/)           | [shenmue-ii](../../content/games/shenmue-ii.md)                                                                           |
| Sakura Taisen 3                  | JP v1.003 disc 1 (2001, Sega)               | [`sakura3/`](sakura3/)             | [sakura-taisen-3-paris-wa-moete-iru-ka](../../content/games/sakura-taisen-3-paris-wa-moete-iru-ka.md)                     |
| Street Fighter III 3rd Strike    | JP v1.003 (2000, Capcom)                    | [`sf3/`](sf3/)                     | [street-fighter-iii-3rd-strike](../../content/games/street-fighter-iii-3rd-strike.md)                                     |
| Ikaruga                          | JP v1.002 (2002, ESP)                       | [`ikaruga/`](ikaruga/)             | [ikaruga](../../content/games/ikaruga.md)                                                                                 |
| Crazy Taxi 2                     | US v1.004 (2001, Sega)                      | [`crazytaxi2/`](crazytaxi2/)       | [crazy-taxi-2](../../content/games/crazy-taxi-2.md)                                                                       |
| Typing E-Keikaku                 | JP v1.001 (2001, Gainax)                    | [`eva-typing/`](eva-typing/)       | [shinseiki-evangelion-typing-e-keikaku](../../content/games/shinseiki-evangelion-typing-e-keikaku.md)                     |
| Jet Set Radio                    | JP (2000, Sega), Redump                     | [`jsr/`](jsr/)                     | [jet-set-radio](../../content/games/jet-set-radio.md)                                                                     |
| Marvel vs. Capcom 2              | JP (2000, Capcom), Redump                   | [`mvc2/`](mvc2/)                   | [marvel-vs-capcom-2](../../content/games/marvel-vs-capcom-2.md)                                                           |
| Resident Evil Code: Veronica     | JP and EU disc 1 (2000, Capcom), Redump     | [`cvx/`](cvx/)                     | [resident-evil-code-veronica](../../content/games/resident-evil-code-veronica.md)                                         |
| Metropolis Street Racer          | EU Rev B (2000, Sega), Redump               | [`msr/`](msr/)                     | [metropolis-street-racer](../../content/games/metropolis-street-racer.md)                                                 |
| Sonic Shuffle                    | JP (2000, Sega), Redump                     | [`sonic-shuffle/`](sonic-shuffle/) | [sonic-shuffle](../../content/games/sonic-shuffle.md)                                                                     |
| Soul Calibur (partly imported)   | US v1.000 (1999, Namco)                     | [`soulcalibur/`](soulcalibur/)     | [soul-calibur](../../content/games/soul-calibur.md)                                                                       |
| Visual Memory Unit, Dreamcast    | US v1.05, JP v1.004 VMU BIOS, `dc_boot.bin` | [`bios/`](bios/)                   | [visual-memory-unit](../../content/games/visual-memory-unit.md), [dreamcast](../../content/games/dreamcast.md)            |
