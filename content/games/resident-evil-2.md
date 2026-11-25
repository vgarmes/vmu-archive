# Resident Evil 2

Scripts: `tools/disc-extraction/re2/`.

Dumps: Redump `Resident Evil 2 (Europe) (En,Fr) (Disc 1)` (T-7004D-50
V1.000, 2000-02-22) and `Biohazard 2 - Value Plus (Japan) (Disc 1)` (T-1214M
V1.005, 1999-11-14), each a `.cue` and six `.bin` tracks. The addresses below
are the European program's unless said.

## Japan and Europe

The European release carries its VMU art in English and French; the Japanese
one has one set, with no suffix on the names (`VTITLE`, `VSAVE`,
`VCONDITIONS`…). Of that set:

- ACCESS, CONNECT, the digits and all 13 save icons are the European English
  ones, byte for byte.
- The title says BIOHAZARD2 where Europe's says RESIDENT EVIL2.
- The condition labels are the same English words, but the AMMO band reads
  のこり (remaining).
- The weapon names are in katakana (コンバットナイフ, ハンドガン…).

So the Japanese title, status screens and those two sprites are `ntsc-j`.
Nothing else is marked as one region's: the American disc wasn't checked, so
the European English pieces get no region, and neither do the French ones.

The Japanese program draws the same status screen from its set: the code
(`0x11A874`) has the same rows, label offsets, blinking, 500 ms check
(`0x11A8AE`) and no-weapon test, and the same copy (`0xC7440`) and digit
lookup (`0x11A7BC`), byte for byte. It draws the AMMO band after the label
instead of before, which changes nothing, and has no language switch.

## What's on the disc

This is a Windows CE game, like Shinseiki Evangelion: Typing E-Keikaku. There
is no `1ST_READ.BIN`: the game is `BIO2DC.EXE`, an SH-4 PE file with image
base `0x10000`, started by Windows CE (`0WINCEOS.BIN`). It reaches the VMU
through `MAPLEDEV.dll`. No file on the disc has a VMU-ish name: the art is in
the EXE's resources, 23 of type `BM`:

| Resource                          | What                                                                        |
| --------------------------------- | --------------------------------------------------------------------------- |
| `VTITLE`                          | The title screen                                                            |
| `VSAVE_ENG`, `VSAVE_FRA`          | ACCESS, ACCES                                                               |
| `VCONNECT_ENG`, `VCONNECT_FRA`    | CONNECT, CONNEXION                                                          |
| `VCONDITIONS_ENG`, `_FRA`         | Fine, Caution, Danger, Poison and AMMO (OK, Faible, Danger, Poison and MUN) |
| `VWEAPONS_ENG`, `_FRA`            | 16 weapon names and a row of dashes                                         |
| `VNUMBERS`                        | The digits 0–9, %, - and ∞                                                  |
| `ORLN` … `ARCU`, `EX…`, `SYSICON` | The save icons (below)                                                      |

The art is 1 bit a dot, a set bit lit, in rows of 8 bytes: 6 of dots, 2 of
padding, and 2 zero bytes after the last row. Each row is stored mirrored.
The game copies a piece into the 192-byte buffer the VMU's LCD takes from the
bottom row up, so the buffer is the art turned 180°, the way the LCD shows it.
Upright, each piece is its rows mirrored back.

## How the screens are shown

At start (`0x11DAAC`) the game finds, loads and copies each `V…` resource
into memory (`FindResource`, `LoadResource`, `LockResource`). `0xC89CC`
copies a block of one into a VMU's buffer, `0xC89B8` clears it and
`0xC8960` sends it. The game keeps four VMU slots.

**The status screen.** `0x11DE64` runs at most every 500 ms (it compares
`GetTickCount`, COREDLL ordinal 535, with the last time). For each slot it
draws:

- On the VMU in the controller being played with (slot `[0x31C480]`), when
  `0xCFA10` allows it (in play, it seems), the status screen: the equipped weapon's name at row 2, the AMMO
  band at row 12 with the ammo count on its right, and the condition at row 22. Fine and the first Caution stay; the second Caution, Danger and Poison
  are drawn on every other update, so they blink at 500 ms. The weapon
  (`0x11730C`) picks its name, 9 rows a weapon; with none (99) the name and
  count are dashes. The count is up to three digits, `%` after the Spark Shot,
  Sub-Machine Gun, Flamethrower and Gatling Gun, and ∞ for unlimited ammo
  (a count of 255).
- On the VMU being saved to or loaded from, ACCESS; while another flag is
  set, CONNECT on the selected VMU (what sets it wasn't traced).
- Otherwise, the title.

`[0x31C488]` picks English or French. `0x11DD4C` also draws ACCESS, CONNECT
or the title on the first VMU directly.

The archive keeps the title, ACCESS and CONNECT, and the status screen for
each condition with no weapon equipped, as drawn by re-running the game's
copy: a count would be a made-up number. The blinking ones are two frames,
with and without the label, 500 ms each. The parts are kept whole as sprites,
so every weapon name and digit is in the archive: the condition labels and
weapon names (9 rows each), and the digits as a font, one under the next in
the game's order: 0–9, %, -, and the two halves of ∞ (the game draws ∞ as
its 12th and 13th cells side by side). The four cells after them are empty.

The game's copy (`0xC89CC`) works out where a piece goes as if it were the
screen's full width; a narrower one, a digit, lands a row lower and a column
to the left of where its arguments say. The archive's screens are drawn the
same way, so they match what the VMU showed.

## Save icons

The save icons are 4-bit 32x32 BMP resources. The save code (`0xF1580`) picks
one by the game mode (`OR…` in one, `AR…` in the other), the character (`L`
Leon, `C` Claire) and the scenario (`N` first, `U` second), or the Extreme
Battle character (`EXLEON`, `EXCLAIRE`, `EXADA`, `EXCHRIS`); the system file
uses `SYSICON`. The game reads 16 colours from where each BMP's palette
starts, so `SYSICON`, which has 13, gets its first pixel bytes as the last
three: that's what dumped saves hold.

| Resource                      | Archive entry, from a save                             |
| ----------------------------- | ------------------------------------------------------ |
| `ORLN`                        | Save file (RE2/OHT/Factory)                            |
| `ORLU`                        | Save file (RE2/ONB/Scenario 2nd)                       |
| `ORCN`                        | Save file (RE2/OET/Dark Room)                          |
| `ORCU`                        | new, rebuilt from the disc                             |
| `ARLN`                        | Save file (RE2/ART/Control Room2)                      |
| `ARLU`                        | Save file (RE2/AEB/Scenario 2nd)                       |
| `ARCN`                        | Save file (RE2/ART/Scenario 1st)                       |
| `ARCU`                        | Save file (ＢＨ２／ＡＥ裏／シナリオ　２ｎｄ), Japanese |
| `EXLEON`, `EXCLAIRE`, `EXADA` | new, rebuilt from the disc                             |
| `EXCHRIS`                     | Save file (RE2/E1 /Dark Room)                          |
| `SYSICON`                     | System file                                            |

All nine already in the archive match byte for byte, the Japanese save's
too, and the Japanese disc holds the same 13 resources, so the icons are the
same in both releases. The rebuilt saves carry the European program's fixed
part of the names (RESIDENT EVIL2, RE2/; the Japanese one has BIOHAZARD2,
ＢＨ２／) and speed 15, as the dumped ones have; the game adds the mode,
difficulty and room when it saves.
