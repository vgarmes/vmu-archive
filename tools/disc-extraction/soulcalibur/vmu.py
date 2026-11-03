"""Decode Soul Calibur's VMU character pictures from HUMAN.DAT.

    python3 vmu.py <dump folder> <out dir>

HUMAN.DAT is an "olnk" archive:

    u32 count, "olnk", u32 header size, u32 total size, then count x { u32 offset, u32 size }
    (offsets count from the end of the header)

Each character's members are themselves tables: u32 count, then count u32
offsets from the member's start. Entry 6 of a character's member is its VMU set,
compressed with the game's LZ routine at 0x8C0EE76C in 1ST_READ.BIN (see lz()).
It unpacks to 7684 bytes: a u32 (48, the width), then 5 frames of 48x32, one
byte per dot: 15 = lit, 0 = unlit inside the figure, 128 = background. All 95
frames match an independent decode exactly.

Writes lcd/<character>.png (5 frames stacked top to bottom, dark = lit) and
manifest.json. A character's later members (costume variants) repeat the same
set; only the first copy is kept.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'common'))
from disc import Disc  # noqa: E402

FW, FH, FRAMES = 48, 32, 5
SET_ENTRY = 6
# HUMAN.DAT member index // 10 -> character, checked against the decoded art.
CHARACTERS = {
    0: 'Mitsurugi', 1: 'Seung Mina', 2: 'Taki', 3: 'Maxi', 4: 'Voldo', 5: 'Sophitia',
    6: 'Siegfried', 7: 'Rock', 8: 'Hwang', 10: 'Ivy', 11: 'Kilik', 12: 'Xianghua',
    13: 'Lizardman', 14: 'Yoshimitsu', 15: 'Edge Master', 16: 'Nightmare', 17: 'Astaroth',
    18: 'Inferno', 19: 'Cervantes',
}


def lz(src):
    """The game's decompressor (0x8C0EE76C). A flag byte is read low bit first: 1 copies a
    byte, 0 is a reference of two bytes, big-endian: top 5 bits length - 1, low 11 bits
    distance - 1. A flag of 1 means take the next flag byte, 0 ends the data, and 0xFF
    is seven literals in a row."""
    out = bytearray()
    i = 0
    while True:
        f = src[i]
        i += 1
        if f == 0:
            return bytes(out)
        if f == 0xFF:
            out += src[i:i + 7]
            i += 7
            continue
        while f != 1:
            if f & 1:
                out.append(src[i])
                i += 1
            else:
                v = src[i] << 8 | src[i + 1]
                i += 2
                length, dist = ((v >> 11) - 1 & 31) + 1, (v - 1 & 0x7FF) + 1
                for _ in range(length):
                    out.append(out[-dist])
            f >>= 1


def members(b):
    count, tag, header, _ = struct.unpack_from('<I4sII', b, 0)
    assert tag == b'olnk', 'not an olnk archive'
    for k in range(count):
        off, size = struct.unpack_from('<II', b, 16 + k * 8)
        yield k, b[header + off:header + off + size]


def main(dump, out):
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    disc = Disc(dump)
    f = next(x for x in disc.files() if x['path'] == '/HUMAN.DAT')
    human = disc.read(f['lba'], f['size'])
    manifest, seen = [], set()
    for k, m in members(human):
        name = CHARACTERS.get(k // 10)
        if not name or name in seen or len(m) < 4 + 4 * (SET_ENTRY + 1):
            continue
        count = struct.unpack_from('<I', m, 0)[0]
        offs = list(struct.unpack_from(f'<{count}I', m, 4)) + [len(m)]
        raw = lz(m[offs[SET_ENTRY]:offs[SET_ENTRY + 1]])
        assert len(raw) == 4 + FRAMES * FW * FH and struct.unpack_from('<I', raw)[0] == FW, f'member {k}'
        px = raw[4:]
        assert set(px) <= {0, 15, 128}, f'member {k}: values {sorted(set(px))}'
        seen.add(name)
        im = Image.new('L', (FW, FH * FRAMES))
        im.putdata([0 if v == 15 else 255 for v in px])
        stem = name.lower().replace(' ', '-')
        im.save(out / 'lcd' / f'{stem}.png')
        manifest.append(dict(character=name, file=f'{stem}.png', member=k, frames=FRAMES))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    print(len(manifest), 'characters ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
