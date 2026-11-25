# Guilty Gear X

Scripts: `tools/disc-extraction/guilty-gear-x/`.

Dump: Redump `Guilty Gear X (Japan)` (`.cue` and 38 `.bin` tracks, most of
them music; T-2402M V2.000, 2000-11-13). The Dreamcast version came out in
Japan alone, so its pieces are `ntsc-j`.

## What's on the disc

`1ST_READ.BIN` runs from `0x8C010000` and links Sega's `pdLcd` library
(version 1.04, the same build as Resident Evil 3's; its write, `0x8C0C6738`,
was found by its bytes). The game shows one screen on the VMU and never
changes it: the Guilty Gear X logo, a skull over the name, at `0x8C0AA25E`.
It's 1536 bytes, a byte a dot, 8 lit and 0 not, stored as shown.

The game loads the library's write in one place, `0x8C081384`, in a routine
(`0x8C08134E`) that sends that screen to one VMU (number 1 in the library's
numbering). It first checks one is there (`0x8C0C67E8`) and asks its
orientation (`0x8C0C66CC`), passing a flag so the library turns the screen as
needed. Of the library, the game uses only those three routines.
`0x8C076696` calls it every 60th time it runs, from the game's main loop
(`0x8C0764B8`), so the logo is sent again about once a second, which also
covers a VMU plugged in later.

The files with VMU-ish names aren't VMU screens. `/VMEM.BIN` is loaded whole
(`0x8C088586`) and its two blocks, at `0x200` and `0x700`, go to the same
routines as the blocks of the file loaded beside it (`0x8C08860C`); its data
looks like 16-bit colours, not dots.
`/DPTEX/VMSPARTS.PVR` and `VMSPART2.PVR` belong to the web browser the disc
carries (`2_DP.BIN`).

## Save icons

The game keeps one save, `DCGUILTY.DAT`, built at `0x8C081090`. Its
description is always ギルティギアゼクス for ＤＣ (`0x8C0AA94C`); its icon and
VMU name come from a table at `0x8C0AA85E` (36 bytes an entry: the icon's
file, its frame count and speed, the name), picked by the unlock byte at
`0x8C0EFB51`. The names say what each level means:

| Level | Icon file      | VMU name       | Frames, speed | Archive entry                  |
| ----- | -------------- | -------------- | ------------- | ------------------------------ |
| 0     | `VMICON01.ICO` | ｷﾞﾙﾃｨﾕｰｻﾞｰﾃﾞｰﾀ | 2, 1          | Save file (nothing unlocked)   |
| 1     | `VMICON02.ICO` | ﾃｽﾀﾒﾝﾄ ｼﾖｳｶﾉｳ  | 2, 1          | Save file (Testament unlocked) |
| 2     | `VMICON03.ICO` | ﾃﾞｨｽﾞｨｰ ｼﾖｳｶﾉｳ | 2, 10         | Save file (Dizzy unlocked)     |
| 3     | `VMICON03.ICO` | GGﾓｰﾄﾞｼﾖｳｷｮｶ   | 2, 10         | the same                       |

Each `.ICO` is a 16-colour ARGB4444 palette and two 32x32 frames at 4 bits a
dot (1056 bytes). `VMICON01` is Faust and `VMICON02` a spiky-haired fighter,
Sol by the look of him, each with its two frames the same; `VMICON03` is that
face and then a silhouette outlined in red.

- **Confirmed.** The icon already in the archive, read from a dumped save
  named ﾃﾞｨｽﾞｨｰ ｼﾖｳｶﾉｳ, is `VMICON03.ICO`, palette and frames byte for byte.
  It's now titled Save file (Dizzy unlocked).
- **Added.** The other two, rebuilt as the game writes them, from their files
  and the table.
