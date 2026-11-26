# Grandia II

Scripts: `tools/disc-extraction/grandia-2/`.

Dumps: Redump `Grandia II (Japan)` (`.cue` and three `.bin` tracks; T-4503M
V1.001, 2000-06-13) and `Grandia II (Europe)` (`.cue` and five `.bin`
tracks; T-17715D V1.000, 2000-12-07). The American disc wasn't checked.

The two discs show the same four screens and differ in two: the logo and the
accessing message. Japan's, with Japanese text, are `ntsc-j`; Europe's
English ones are left unmarked, since nothing shows the American disc lacks
them. NG and OK are the same bytes on both.

## What's on the disc

No file has a VMU-ish name. The screens are in the program itself:
`1ST_READ.BIN` runs from `0x8C010000` and links Sega's `pdLcd` library
(version 1.04, built 1999-04-26 16:55:25, the build Guilty Gear X and
Resident Evil 3 link). The rest of the game runs as overlays the program
loads from `/BIN/`: the title screen (`GR2TITLE.BIN`) and the field
(`FIELD.BIN`), both from `0x8C380000`, battles (`BATTLE.BIN`) and a few
more.

There are four screens, back to back, at `0x8C019588` on the Japanese disc
and `0x8C0195A8` on the European. Each is 192 bytes, a bit a dot, the
leftmost dot in a byte's top bit, turned 180°, as the LCD takes it:

| Number | Japan                                               | Europe                                    |
| ------ | --------------------------------------------------- | ----------------------------------------- |
| 0      | The logo: グランディアII, outlined, over ©GAME ARTS | The logo: GRANDIA over II, white on black |
| 1      | NG                                                  | NG                                        |
| 2      | OK                                                  | OK                                        |
| 3      | アクセス中 ("accessing")                            | Accessing                                 |

After the fourth come 24 empty bytes and a table of pointers, so there's no
fifth.

## How the screens are shown

Addresses are the Japanese disc's; the European program keeps the game's
own routines where they are and moves the library and the data by `0x20`
(the number is at `0x8C148508`).

The game's send (`0x8C010B3E`) takes a list of screens and a screen number,
held in `0x8C1484E8`. For each of the eight places a VMU can be, it checks
one with a screen is there (the library's `0x8C038698`) and sends it the
numbered screen with the library's write for packed screens (`0x8C03864E`),
which sends the bytes as they are: the game never asks the VMU's
orientation. It sends only when the number changed or a VMU was newly
plugged in. Its one caller, `0x8C01051E`, passes it the four screens. Of the
library, the game uses only those two routines; the write that turns a
screen first (`0x8C0385E8`) is linked but never called.

The overlays reach the program through tables that start-up (`0x8C010080`)
copies to fixed addresses near the top of memory: `0x8CFFDE00` holds the
reset (`0x8C0104CA`, which sets the number to 0) and the send, and
`0x8CFFF010` a pointer to the number. All the overlays but the copyright
screen's call the send (the title's from its main loop, `0x8C3804DC`). Only
the title and field overlays change the number, and they pick it with the
same code, in their save and load menus (from `0x8C381790` in the title's,
`0x8C3D3D2A` in the field's; `0x8C3817B4` and `0x8C3D505E` on the European
disc):

- **The logo** is what the VMU shows the rest of the time.
- **Accessing** while the memory card is read or written (states 2 to 4 of
  the menu; the European disc adds state 5).
- **OK** or **NG** when that finishes, by whether it worked, held until a
  count the menu steps once a pass reaches a limit, then the logo again. The
  limit is 120 on the Japanese disc (two seconds, if the menu runs at
  60 Hz) and 15 on the European; what paces the European menu wasn't
  traced.

The European overlays also set the number in a few more places, always to
the logo or Accessing, and only show Accessing over the logo, never over an
OK or NG still up.

None of the screens animates.

## Save icons

The game's save icons are in `/WINDOW/SAVEICON.AFS`: nine members of 544
bytes, each a 16-colour palette and a 32x32 picture at 4 bits a dot, all
portraits: Ryudo, Elena, Millenia, Roan, Tio, Mareg, two more characters and
Skye. Eight are already in the archive, read from dumped saves (their
descriptions name the place a save was made, not who's pictured); Skye's,
the last member, isn't. Which portrait a save gets wasn't traced.
