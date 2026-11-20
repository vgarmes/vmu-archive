# Record of Lodoss War

Dump: `Record of Lodoss War - The Advent of Cardice (Japan) (Rev A)` (Redump,
`.cue` and three `.bin` tracks), ロードス島戦記 邪神降臨. Its boot file is
`1NOSDC.BIN`, not `1ST_READ.BIN`; it loads at `0x8C010000`.

The game draws nothing on the VMU, so there's nothing to import and no game
page to hold notes; the findings are here. `check.py` prints the evidence and
checks the archive's save icon.

## Run

```sh
DUMP="path/to/Record of Lodoss War - The Advent of Cardice (Japan) (Rev A)"
OUT=/tmp/lodoss
python3 -E ../common/disc.py "$DUMP" $OUT/files /1NOSDC.BIN
python3 -E check.py $OUT/files/1NOSDC.BIN
```

Run the Python script from this folder. It doesn't need Pillow.

## The VMU screen

The game clears each VMU's screen once and leaves it.

The program links Sega's `pdLcd` library (version 1.04, built 1999-04-26),
which takes a screen as 1,536 bytes, a byte a dot. Its write (`0x8C2AAF04`) is
loaded in one place, the game's send at `0x8C013E80`. That routine sends the
screen it's given, or, given none, clears a buffer at `0x8C3B4E0E` and sends
that, a blank screen. Its one caller, the loop at `0x8C014004`, passes the
pointer kept at `0x8C3B5450` and sends again only when a flag says the pointer
changed. Setup (`0x8C014204`) zeroes that pointer, and the only code that sets
it, `0x8C013C6E`, is never called: nothing on the disc holds its address.

So each VMU gets one blank screen. No screen in either form (1 bit a dot, or a
byte a dot) turned up in the program or the data files.

## Save icon

The save header is built at `0x8C0C70AE`: one icon, its frame at `0x8C1426B8`
and palette at `0x8C1428B8`, one frame at animation speed 0, with the names
from a table at `0x8C141894` (ﾛｰﾄﾞｽﾄｳｾﾝｷ, ロードス島戦記 邪神降臨).

- **Confirmed.** The save icon already in the archive, read from a dumped save
  (`LODOSS__.002`), is the game's own: its frame and palette match the
  program's byte for byte.
