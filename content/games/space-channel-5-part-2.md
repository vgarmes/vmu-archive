# Space Channel 5: Part 2

Scripts: `tools/disc-extraction/space-channel-5-part-2/`.

Dump: Redump `Space Channel 5 Part 2 (Japan)` (`.cue` and three `.bin`
tracks; HDR-0190 V2.000, 2001-12-09). The Dreamcast release was Japan's
alone (elsewhere Part 2 came out on the PlayStation 2), so its pieces are
`ntsc-j`.

## What's on the disc

No file holds VMU art. It's in `1ST_READ.BIN`, which runs from `0x8C010000`
and links Sega's `pdLcd` library (version 2.00). Unlike the first game, it
doesn't use `vmslcd.c`: a small manager of its own (one object, kept at
`0x8C240414`) holds a screen number for the VMUs in ports A and B, and every
frame sends that screen with `pdLcd`'s write for packed screens
(`0x8C0167DA`). The overlays (`TITLE.BIN`, `R0.BIN` to `R6.BIN`) never call
it.

There are three screens, 192 bytes each from `0x8C133AE0`, packed 1 bit a dot
and turned 180°, the way the LCD takes them. Their pointers follow them, at
`0x8C133D20`.

| Screen | Shown                                                     | Archive entry  |
| ------ | --------------------------------------------------------- | -------------- |
| 0      | the resting screen: `set(0)`, and whenever none is chosen | Channel 5 logo |
| 1      | `set(1)` at `0x8C0D1FDE`                                  | Now loading    |
| 2      | `set(2)` at `0x8C0D245E`                                  | Now saving     |

`set` is `0x8C0E6730`. The logo has Part2 written under it; the loading and
saving screens look like the first game's but aren't pixel for pixel the
same.

## Save icon

The save header is prebuilt at `0x8C12C190` (used at `0x8C0D254A`) for its
one save, `SC5PART2_DAT`: palette at `0x8C12BCF8`, two frames at
`0x8C12BD18`, animation speed 10.

- **Confirmed.** The save icon already in the archive, read from a dumped save,
  is the game's own: its palette and both frames match the program's byte for
  byte.
