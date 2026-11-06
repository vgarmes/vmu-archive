# Resident Evil Code: Veronica

Dump: `Biohazard - Code - Veronica (Japan) (Disc 1)` (Redump, `.cue` and
three `.bin` tracks).

The game has no VMU screens in the archive yet, so no page and no notes file
(`content/games/` only takes games with screens). Until it does, its findings
are kept here; move them to `content/games/resident-evil-code-veronica.md`
when the screens are added.

## Run

```sh
DUMP="path/to/Biohazard - Code - Veronica (Japan) (Disc 1)"
OUT=/tmp/cvx
python3 -E ../common/disc.py "$DUMP" $OUT/files /1ST_READ.BIN
python3 -E saves.py $OUT/files/1ST_READ.BIN   # checks the archive's save icons
```

Run the Python scripts from this folder.

## Save icons

No file on the disc holds them. The three icons the game writes sit back to
back in `1ST_READ.BIN` (runs from `0x8C010000`), each a palette then its
frames, exactly as the save header takes them. All three match the archive's
entries byte for byte, though those came from dumped saves (two Japanese, one
American):

| Icon                  | Address      | Frames, speed | Loaded at    | Archive entry |
| --------------------- | ------------ | ------------- | ------------ | ------------- |
| Zombie face           | `0x8C13BC20` | 1, 30         | `0x8C12BE64` | `system-file` |
| CODE: Veronica, red   | `0x8C13BE40` | 3, 30         | `0x8C128BA0` | `save-file-2` |
| CODE: Veronica, olive | `0x8C13C460` | 3, 30         | `0x8C128BAA` | `save-file`   |

The system file is `VERONICA.SYS`, named `VERONICA.SYS` on the card with the
description `BIO_CV/ｼｽﾃﾑﾃﾞｰﾀ` (system data). A game save is `VERONICA.%03u`,
named `BIO_%02u_GAMEDATA`, its description built from the character, the
difficulty (`N/`, `E/`, `V/`) and the room name. The builder at `0x8C128ACA`
reads the character from byte `+0x84` of the game state: 0 writes `BIO_CV/ｸﾚｱ/`
(Claire), 1 `BIO_CV/ｸﾘｽ/` (Chris), 2 `BIO_CV/ｵﾏｹ/` (bonus). The same byte picks
the icon: Claire's saves get the red one, every other save the olive one. The
saves the archive's entries came from agree: the red one is from a
`BIO_CV/ｸﾚｱ/…` save, the olive one from an American `RE_CV/CHRIS/…` save.
Since the Japanese program holds both, neither is region-only.

The program also has a routine that writes a memory card icon,
`ICONDATA_VMS` (`0x8C12C910`), but nothing calls it.

## VMU screens (not imported yet)

The game's VMU art is one 128x128 1-bit sheet in `1ST_READ.BIN` at
`0x8C13CEFC`, 16 bytes a row, as shown (bit 7 leftmost, 1 lit): the
BIOHAZARD / CODE: Veronica logo, heartbeat traces, FINE, CAUTION, DANGER, DIED,
POISON, SAVE, LOAD, OK, NG, three YOU DIED, Mission Clear! and 32x32 portraits
of Claire, Chris, Steve and Wesker. A table of 56 rectangles follows it at
`0x8C13D6FC` (x, y, width, height as 16-bit values), then what looks like a
script of (routine, argument) pairs at `0x8C13D8C4`. `0x8C12CB6C` sets the
sheet up. How the screens are put together and timed hasn't been traced.
