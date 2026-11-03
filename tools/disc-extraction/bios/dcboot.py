"""Decode the memory card icons built into the Dreamcast BIOS.

    python3 dcboot.py <dc_boot.bin> <out dir>

dc_boot.bin is the console's 2 MB boot ROM. From 0x17EF50 it holds 129
monochrome icons, 32x32, 128 bytes each (4 bytes a row, high bit first,
1 = lit, upright). Before the set and after it the bytes are noise, so the
bounds are where the art stops. These are the icons the BIOS memory card
screen offers ("Please use the controller to select an icon"); it shows them
on the TV, not on the VMU, so they're kept as sprites.

Writes NNN-<name>.png per icon, manifest.json and contact-sheet.png.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import png

START, COUNT, SIZE = 0x17EF50, 129, 128
# The dump this was read from: the common dc_boot.bin.
MD5 = 'e10c53c2f8b90bab96ead2d368858623'

# (name, tags) in ROM order; the digits, letters and patterns are filled in below.
NAMES = [
    ('Circled cross', []), ('Hourglass, frame 1', []), ('Hourglass, frame 2', []),
    ('Hourglass, frame 3', []), ('Hourglass, frame 4', []), ('Visual Memory', []),
    ('Earth', []), ('Ringed planet', []), ('Crescent moon', []),
    ('Laughing face', ['face']), ('Smiling face', ['face']), ('Blank face', ['face']),
    ('Squinting face', ['face']),
    ('Cow', ['animal']), ('Horse', ['animal']), ('Rabbit', ['animal']), ('Cat', ['animal']),
    ('Chick', ['animal']), ('Lion', ['animal']), ('Monkey', ['animal']), ('Panda', ['animal']),
    ('Bear', ['animal']), ('Pig', ['animal']), ('Dog', ['animal']), ('Fish', ['animal']),
    ('Octopus', ['animal']), ('Squid', ['animal']), ('Whale', ['animal']), ('Crab', ['animal']),
    ('Butterfly', ['animal']), ('Ladybird', ['animal']),
    ('Round face with gears', ['unidentified']),
    ('Penguin', ['animal']),
    ('Cherries', []), ('Tulip', []), ('Leaf', []), ('Cherry blossom', []), ('Apple', []),
    ('Cupcake', []), ('Cactus', []),
    ('Piano', ['music']), ('Guitar', ['music']), ('Musical note', ['music']),
    ('Treble clef', ['music']),
    ('Sailing boat', ['vehicle']), ('Car', ['vehicle']), ('Helmet', []),
    ('Motorbike', ['vehicle']), ('Van', ['vehicle']), ('Lorry', ['vehicle']),
    ('Clock', []), ('Telephone', []), ('Pencil', []), ('Mug', []), ('Knife and fork', []),
    ('House', []), ('Bell', []), ('Crown', []), ('Sock', []), ('Birthday cake', []),
    ('Key', []), ('Book', []), ('Bat and ball', []), ('Football', []), ('Light bulb', []),
    ('Teddy bear', []), ('Bow', []), ('Bow and arrow', []), ('Snowman', []),
    ('Lightning', ['weather']), ('Sun', ['weather']), ('Cloud', ['weather']),
    ('Umbrella', ['weather']),
    ('One star', ['star']), ('Two stars', ['star']), ('Three stars', ['star']),
    ('Four stars', ['star']),
    ('Heart', ['cards']), ('Diamond', ['cards']), ('Spade', ['cards']), ('Club', ['cards']),
    ('Jack', ['cards']), ('Queen', ['cards']), ('King', ['cards']), ('Joker', ['cards']),
    ('Palm tree', []),
]
NAMES += [(f'Digit {d}', ['digits']) for d in range(10)]
NAMES += [(f'Letter {chr(65 + i)}', ['letters']) for i in range(26)]
NAMES += [(p, ['pattern']) for p in ('Checkerboard', 'Grid', 'Fine dots', 'Diagonal lattice',
                                     'Nested squares', 'Fine checkerboard', 'Diamond lattice')]
assert len(NAMES) == COUNT, len(NAMES)


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def main(src, out):
    rom = Path(src).read_bytes()
    md5 = hashlib.md5(rom).hexdigest()
    if md5 != MD5:
        print(f'warning: {src} has md5 {md5}, not the {MD5} this was read from')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for i, (name, tags) in enumerate(NAMES):
        off = START + i * SIZE
        im = png.bits(rom[off:off + SIZE], 32, 32)
        stem = f'{i:03d}-{slug(name)}'
        png.save(out / f'{stem}.png', im)
        manifest.append(dict(name=stem, index=i, what=name, tags=tags, offset=off))
        images.append(im)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    png.save(out / 'contact-sheet.png', png.sheet(images, 16), scale=3, gap=160)
    print(COUNT, 'icons from', hex(START), '->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
