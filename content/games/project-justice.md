# Moero! Justice Gakuen

Scripts: `tools/disc-extraction/justice/`.

Dump: `Moero! Justice Gakuen v1.004 (2000)(Capcom)(JP)[!][1M4]` (`.gdi`). The
archive files these under `Project Justice`. The disc carries both the Japanese
and the English (Project Justice) screens, so region follows the logo: `JP` on
the Japanese pair, none on the Project Justice pair, which was the US and
European title.

## What's on the disc

No file on the disc holds VMU art. The screens are in `1ST_READ.BIN`, found by
searching every file for the archive's Project Justice title screen, which
matches screen 2 exactly.

The game uses the `0x0C000000` alias of main RAM, so `1ST_READ.BIN` loads at
`0x0C010000` and `common/find_code.py` (which assumes `0x8C010000`) can't see its
references. A table at `0x0C1F5AB0`, after the save-file descriptors, points at
four screens stored upright in the archive's own encoding (1 bit per pixel, high
bit first).

| Screen | Shows | Archive entry |
| --- | --- | --- |
| 0 | Moero! Justice Gakuen logo | Title screen (JP) |
| 1 | ACCESS, under that logo | Access (JP) |
| 2 | Project Justice logo | Title screen (already in the archive) |
| 3 | ACCESS, under that logo | Access |

`0x0C033BD6` picks the pair: screens 0 and 1 when the byte at `0x0C3E0028` is 0,
2 and 3 otherwise. What sets that byte wasn't traced; it reads like a language
or console-region setting. The archive's Project Justice title screen matches
screen 2 exactly, so the releases likely share one set of screens. `0x0C021474` redraws the current screen on every VMU every 64 calls, and
`0x0C021540` shows ACCESS on one VMU at once. Nothing animates, and every screen
is reachable, so none is marked unused.
