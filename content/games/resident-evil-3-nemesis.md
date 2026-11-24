# Resident Evil 3: Nemesis

Scripts: `tools/disc-extraction/re3/`.

Dumps: Redump `Biohazard 3 - Last Escape (Japan)` (T-1222M V1.002,
2000-09-13) and `Resident Evil 3 - Nemesis (Europe)` (T-7021D-05 V1.000,
2000-11-14), each a `.cue` and three `.bin` tracks. The addresses below are
the Japanese program's.

## Japan and the West

The only difference on the VMU is the title. Japan's says BIOHAZARD3 / LAST
ESCAPE, so it's kept as `ntsc-j`; Europe's says RESIDENT EVIL3 / NEMESIS in
the same style. The other 44 screens are the same bytes in both and get no
region.

The European disc carries three sets of the VMU files. `RETENUTO/DC` is the
Japanese set, byte for byte, title included. `RETENUTO/DC_E` and `DC_U` are
identical to each other, with the Western title. The European program only
names `RETENUTO/DC_e/vms_1.DCL` (and its icons) and never the other two.
`DC_U` is by its name the American set: the American disc wasn't checked,
but this is why the Western title gets no region rather than `pal`.

The European program's VMU code is the Japanese one moved, instruction for
instruction except for the pointers it loads. The picker is at `0x8C153304`,
the routine that runs the VMU at `0x8C1540C4`, and the file's name at
`0x8C17CE70`.

## What's on the disc

`1ST_READ.BIN` runs from `0x8C010000` and links Sega's `pdLcd` library
(version 1.04). The VMU art is a file of its own, `/RETENUTO/DC/VMS_1.DCL`
(`RETENUTO` holds the Dreamcast port's own files): 45 screens of 48x32, one
byte a dot, `0x0F` lit and 0 not, stored as shown, 1536 bytes each, nothing
else. The loader (`0x8C02D018`) reads the whole file into the VMU code's work
area at `+0x34B4` and points a table at `+0x142B4` at each screen.

| Screens | Shows                                       | Archive entry               |
| ------- | ------------------------------------------- | --------------------------- |
| 0–3     | ACCESS, CONNECT, Ok, Error                  | Access, Connect, Ok, Error  |
| 4       | BIOHAZARD3 / LAST ESCAPE                    | Title screen                |
| 5–8     | Portraits: Jill, Carlos, Mikhail, Nikolai   | one each                    |
| 9–20    | FINE, CAUTION, DANGER, a 4-frame trace each | Condition: Fine, and so on  |
| 21–32   | POISON over the same three traces           | Condition: Poison (fine), … |
| 33–44   | VIRUS over the same three traces            | Condition: Virus (fine), …  |

The other files with VMU-ish names aren't VMU screens: `/DPTEX/VMSPARTS.PVR`
and `VMSPART2.PVR` are colour textures in the folders of the web browser the
disc carries (`2_DP.BIN`), and `/BIO19/DATA/ETC/ICON.DAT` is a 16-dot-wide
TIM, the PlayStation's image format, with a 16-colour palette. The two `.DCB`
files are the save icons (below).

## How the screens are shown

`0x8C02DCC0` runs the VMU, once a pass of the game's frame routine. It keeps
a state and a counter (`0x8C514D60`), and sends a screen to every VMU
(`0x8C02CBB0`) or to the one being used (`0x8C02CBA4`).

**Memory card.** When the game opens a card it shows ACCESS. A finished save
or load shows Ok 7 passes later, held 47 passes. A failure shows Error, held
47 passes, except on one path that leaves ACCESS up instead. Each goes back
to the title. If nothing ends the access, the title comes back after 122
passes.

**Play.** Otherwise the VMU updates every 11 passes:

- While bit `0x8000000` of `+0x2120` in the game state at `0x8C966B9C` is
  clear, or any of nine other game-state flags is set, it shows the title.
  The first looks like "in play"; what the others stand for wasn't traced.
- While bit `0x200` of `+0x7804` is set, it shows the player's portrait,
  by the character byte at `+0x24E6`: 8 Carlos, 9 Mikhail, 10 Nikolai,
  anything else Jill. What sets the bit wasn't traced.
- Otherwise it shows the condition monitor. `0x8C02CE30` picks the trace by
  health (`+0x2568`): above 100 FINE, 21 to 100 CAUTION, 20 or less DANGER.
  Status bit `0x100` (`+0x256E`) puts VIRUS under it instead, else bit
  `0x200` POISON. The trace steps through its four frames, one an update, and
  starts again at the same frame when the screen changes.

The archive keeps each trace's four frames as one animation, 183 ms a frame:
11 passes, taking the frame routine to run at 60 Hz. What paces that routine
wasn't traced.

**Unused.** Nothing loads CONNECT, screen 1: the code only ever takes ACCESS,
Ok and Error from the table by number, and the monitor's numbers start at 9.
The browser, `2_DP.BIN`, doesn't name the file.

## Save icons

`/RETENUTO/DC/BIO3_FICON.DCB` and `BIO3_SYSFICON.DCB` are the icons the game
writes into a save and into its system file: a 16-colour ARGB4444 palette,
then three 32x32 frames at 4 bits a dot (1568 bytes). All three of the
archive's entries are on the discs, byte for byte:

| Icon               | Japanese disc (`DC`) | European disc (`DC_E`, `DC_U`) | Archive entry, from a save                   |
| ------------------ | -------------------- | ------------------------------ | -------------------------------------------- |
| Game save, Japan's | `BIO3_FICON.DCB`     | (only the leftover `DC` copy)  | Save file (ＢＨ３／ＡＨ／倉庫オフィス)       |
| Game save, West's  | not there            | `BIO3_FICON.DCB`               | Save file (RE3/EASY/Monitor Room)            |
| System file        | `BIO3_SYSFICON.DCB`  | `BIO3_SYSFICON.DCB`            | System file (ＢＨ３／システム／アップロード) |

So the Japanese game-save icon is `ntsc-j`. The Western one, read from an
American save, is the European disc's too, and the system file's icon is the
same in every set.
