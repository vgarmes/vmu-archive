# Power Stone and Power Stone 2

Dumps:

- `Power Stone v1.020 (1999)(Capcom)(JP)[!][1MB1]` (`.gdi`), release `ps1`
- `Power Stone 2 v2.000 (2000)(Capcom)(JP)[!]` (`.gdi`), release `ps2`

The names and logos are the same in every release, so nothing from these discs
gets a region.

## Run

```sh
PS1="path/to/Power Stone v1.020 (1999)(Capcom)(JP)[!][1MB1]"
PS2="path/to/Power Stone 2 v2.000 (2000)(Capcom)(JP)[!]"
OUT=/tmp/power-stone
python3 -E ../common/disc.py "$PS1" $OUT/ps1 /1ST_READ.BIN
python3 -E ../common/disc.py "$PS2" $OUT/ps2 /1ST_READ.BIN
python3 -E vmu.py ps1 $OUT/ps1/1ST_READ.BIN $OUT/out
python3 -E vmu.py ps2 $OUT/ps2/1ST_READ.BIN $OUT/out
python3 -E prep.py $OUT/out $OUT/inbox                # anything new, ready to import
pnpm icons:import $OUT/inbox
```

Run the Python scripts from this folder.

## What's on the discs

No file holds VMU art. Both games keep two screens in `1ST_READ.BIN`, which
loads at `0x0C010000` (the `0x0C` alias of main RAM, like Moero! Justice Gakuen),
so `common/find_code.py` can't see their references.

Power Stone was found by searching for the archive's title screen, which matched
only with its bits inverted. Power Stone 2 was found by searching for the same
expansion code: each screen has a routine that turns it into a byte buffer
(8 = lit) for the VMU, and the routine sets the polarity.

| Release | Screen | Address      | Routine      | Stored   | Archive entry                                |
| ------- | ------ | ------------ | ------------ | -------- | -------------------------------------------- |
| ps1     | Title  | `0x0C17C198` | `0x0C020174` | inverted | Title screen (already in the archive, exact) |
| ps1     | ACCESS | `0x0C17C258` | `0x0C0201BC` | as shown | Access                                       |
| ps2     | Title  | `0x0C210084` | `0x0C03A670` | as shown | Title screen                                 |
| ps2     | ACCESS | `0x0C210144` | `0x0C03A6B6` | as shown | Access                                       |

All four routines have many callers in the save and load code, so every screen
is shown. Nothing animates.

The archive's Power Stone title came from a screenshot, through an older version
of the importer that read a screenshot's majority colour as unlit. It got this
one right: the disc stores the title inverted, and the game inverts it again
before sending it, so the entry matches the disc exactly.
