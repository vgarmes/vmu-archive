"""Check the archive's Code: Veronica save icons against the disc's program.

    python3 saves.py <1ST_READ.BIN>

The program holds the three icons it writes into a save's header, each a
16-colour ARGB4444 palette followed by its 32x32 frames at 4 bits a pixel, as
in the VMS header (see scripts/import-saves.ts). The addresses are the ones the
save code stores into the header it builds (see
content/games/resident-evil-code-veronica.md). Prints, for each,
the archive entry holding the same palette and frames, and exits non-zero if
one is missing or differs.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GAME_ID = 'resident-evil-code-veronica'  # its id in content/games.json
LOAD = 0x8C010000  # where 1ST_READ.BIN runs from

# (what, palette address, frames, animation speed), as the code sets them:
# 0x8C12BE64 for the system file, 0x8C128B96 for a game save, which picks
# Claire's icon when the character byte (+0x84 of the game state) is 0 and the
# other one for 1 (Chris) and 2 (the bonus mode).
ICONS = [
    ('VERONICA.SYS, BIO_CV/システムデータ', 0x8C13BC20, 1, 30),
    ('game save, Claire', 0x8C13BE40, 3, 30),
    ('game save, Chris or bonus', 0x8C13C460, 3, 30),
]


def palette(b, off):
    out = []
    for i in range(16):
        v = int.from_bytes(b[off + 2 * i:off + 2 * i + 2], 'little')
        a, r, g, bl = (v >> 12) & 15, (v >> 8) & 15, (v >> 4) & 15, v & 15
        out.append('#' + ''.join(f'{n * 17:02x}' for n in (r, g, bl, a)))
    return out


def main(program):
    b = Path(program).read_bytes()
    archive = {}
    for path in (REPO / 'content/save-icons' / GAME_ID).glob('*.json'):
        s = json.loads(path.read_text())
        archive[(tuple(s['palette']), tuple(s['frames']))] = (path.name, s)
    bad = 0
    for what, addr, nframes, speed in ICONS:
        off = addr - LOAD
        pal = palette(b, off)
        frames = [b[off + 0x20 + n * 0x200:off + 0x20 + (n + 1) * 0x200].hex() for n in range(nframes)]
        hit = archive.get((tuple(pal), tuple(frames)))
        if not hit:
            print(f'{addr:#010x} {what}: NOT in the archive')
            bad += 1
            continue
        name, s = hit
        same_speed = s.get('animationSpeed') == speed
        print(f'{addr:#010x} {what}: {name} ({s["title"]}), {nframes} frame(s), '
              f'speed {speed}{"" if same_speed else " (archive has " + str(s.get("animationSpeed")) + ")"}')
        bad += not same_speed
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
