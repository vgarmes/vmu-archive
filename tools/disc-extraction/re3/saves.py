"""Check the archive's Resident Evil 3 save icons against the disc's.

    python3 saves.py <folder with RETENUTO/DC/BIO3_FICON.DCB and BIO3_SYSFICON.DCB>

Each .DCB is the icon the game writes into a save's header: a 16-colour
ARGB4444 palette (32 bytes), then three 32x32 frames at 4 bits a pixel (512
bytes each), as in the VMS header (see scripts/import-saves.ts). Prints, for
each, the archive entry holding the same palette and frames, and exits
non-zero if one is missing.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GAME_ID = 'resident-evil-3-nemesis'  # its id in content/games.json
ICONS = [
    ('game save', 'RETENUTO/DC/BIO3_FICON.DCB'),
    ('system file', 'RETENUTO/DC/BIO3_SYSFICON.DCB'),
]


def palette(b):
    out = []
    for i in range(16):
        v = int.from_bytes(b[2 * i:2 * i + 2], 'little')
        a, r, g, bl = (v >> 12) & 15, (v >> 8) & 15, (v >> 4) & 15, v & 15
        out.append('#' + ''.join(f'{n * 17:02x}' for n in (r, g, bl, a)))
    return out


def main(src):
    archive = {}
    for path in (REPO / 'content/save-icons' / GAME_ID).glob('*.json'):
        s = json.loads(path.read_text())
        archive[(tuple(s['palette']), tuple(s['frames']))] = (path.name, s)
    bad = 0
    for what, name in ICONS:
        b = (Path(src) / name).read_bytes()
        assert len(b) == 0x20 + 3 * 0x200, len(b)
        frames = [b[0x20 + n * 0x200:0x20 + (n + 1) * 0x200].hex() for n in range(3)]
        hit = archive.get((tuple(palette(b)), tuple(frames)))
        if hit:
            print(f'/{name} ({what}): {hit[0]} ({hit[1]["title"]}, {hit[1]["description"]})')
        else:
            print(f'/{name} ({what}): NOT in the archive')
            bad += 1
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
