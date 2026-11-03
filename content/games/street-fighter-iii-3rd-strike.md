# Street Fighter III 3rd Strike

Scripts: `tools/disc-extraction/sf3/`.

Dump: `Street Fighter III 3rd Strike - Fight for the Future v1.003 (2000)(Capcom)(JP)[!]`
(`.gdi`). The name and logo are the same in every release, so nothing from this
disc gets a region.

## What's on the disc

No file holds VMU art (`DPETC/VMS.DPS` belongs to the bundled Dream Passport
browser). The screens are in `1ST_READ.BIN`, which links Sega's `pdLcd`
library. With no screen in the archive to search for, they were found by
drawing the data next to the save-file names (`STF3_3RD.SYS`) as 48-pixel-wide
1-bit rows: four screens sit back to back from `0x8CCB2310`, stored upright in
the archive's own encoding (1 bit per pixel, high bit first). The game runs from
`0x8C010000`, so `common/find_code.py` sees its references.

| State | Address      | Shows      | Archive entry |
| ----- | ------------ | ---------- | ------------- |
| 1     | `0x8CCB2310` | Title logo | Title screen  |
| 2     | `0x8CCB23D0` | ACCESS…    | Access        |
| 3     | `0x8CCB2490` | OK!        | OK            |
| 4     | `0x8CCB2550` | ERROR!     | Error         |

`0x8CB1730A` is the only caller of the routine that sends a screen to a VMU
(`0x8CD50FE0`). For each of the 8 VMU slots whose state byte has changed, it
picks the screen by state, expands it into a byte buffer (8 = lit) and sends it.
What sets each state wasn't traced; the names say when they show (saving and
loading, and its result). Nothing animates, and there are no sprites: every
screen is drawn whole.
