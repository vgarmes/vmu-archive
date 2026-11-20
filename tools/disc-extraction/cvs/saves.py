"""Rebuild Capcom vs. SNK: Millennium Fight 2000's save files from its program.

    python3 saves.py <1ST_READ.BIN> <out dir>

Writes one .VMS per distinct save icon, its header rebuilt the way the game
builds it, and two sidecars for `pnpm saveicons:import`: save-icons.json for
the saves with Japanese names (ntsc-j) and save-icons-color.json for the
colour edit file, which has no text. Also icons.png, the six icons side by
side.

Addresses are for the JP Rev A release; 1ST_READ.BIN loads at 0x8C010000. See
content/games/capcom-vs-snk-millennium-fight-2000.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

LOAD = 0x8C010000

# The header builder, 0x8C067D58, takes a save type (0-15). It zeroes a
# 96-byte record, then a switch (types 0-14, jump table 0x8C067D98) copies
# the VMU name and description into it; every type then takes its palette
# from 0x8C1BAD4C and its frame from 0x8C1BAD8C, with 1 frame at animation
# speed 5. Types 2, 3 and 15 skip the switch and keep blank names.
PALETTES = 0x8C1BAD4C
BITMAPS = 0x8C1BAD8C
SAVES = [
    # type 0
    dict(type=0, title='UPLOAD file', vms=0x8C1B9820, desc=0x8C1B9832),
    # type 1, 2: the System file, already in the archive from a dumped save
    dict(type=1, title='System file', vms=0x8C1B9708, desc=0x8C1B971A),
    # type 3: the switch gives it no names, but the table holds DOWNLOAD's
    # name and description in place, unreferenced, after UPLOAD's; its icon
    # is UPLOAD's with the arrow turned down.
    dict(type=3, title='DOWNLOAD file', vms=0x8C1B9864, desc=0x8C1B9876),
    dict(type=4, title='Capcom network file', vms=0x8C1B98A8, desc=0x8C1B98BA),
    # types 5-14, the ten replays (CAPVSSNK_RD0 to _RD9), share one icon
    dict(type=5, title='Replay file', vms=0x8C1B974C, desc=0x8C1B975E),
    # type 15: past the switch; no names on the disc. Its icon says COLOR
    # (the game has a COLOR EDIT MODE).
    dict(type=15, title='Color edit file', region=None),
]


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def cstr(b, addr, n):
    return at(b, addr, n).split(b'\0')[0]


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    pals = struct.unpack('<16I', at(b, PALETTES, 64))
    bmps = struct.unpack('<16I', at(b, BITMAPS, 64))
    titles, color = {}, {}
    icons = []
    for s in SAVES:
        t = s['type']
        hdr = bytearray(0x80)
        if 'vms' in s:
            hdr[0:16] = cstr(b, s['vms'], 18).ljust(16, b' ')[:16]
            hdr[0x10:0x30] = cstr(b, s['desc'], 34).ljust(32, b' ')[:32]
        struct.pack_into('<HH', hdr, 0x40, 1, 5)
        hdr[0x60:0x80] = at(b, pals[t], 32)
        data = bytes(hdr) + at(b, bmps[t], 512)
        file = f'{t:02d}.VMS'
        (out / file).write_bytes(data)
        (color if 'region' in s else titles)[file] = s['title']
        icons.append((hdr[0x60:0x80], at(b, bmps[t], 512)))
        name = hdr[0:16].decode('shift_jis').rstrip()
        print(f'type {t:2}: {s["title"]:20} {name:16} palette {pals[t]:#x} frame {bmps[t]:#x}')

    base = dict(game='capcom-vs-snk-millennium-fight-2000', publisher='Capcom', year=2000,
                disc='/1ST_READ.BIN')
    (out / 'save-icons.json').write_text(json.dumps(
        dict(**base, region='ntsc-j', titles=titles), ensure_ascii=False, indent=1))
    (out / 'save-icons-color.json').write_text(json.dumps(
        dict(**base, titles=color), ensure_ascii=False, indent=1))

    try:
        from PIL import Image
    except ImportError:
        return
    sheet = Image.new('RGBA', (len(icons) * 104 + 8, 104), (200, 200, 200, 255))
    for k, (pal, bmp) in enumerate(icons):
        cols = []
        for i in range(16):
            c = struct.unpack_from('<H', pal, 2 * i)[0]
            cols.append(tuple(((c >> s) & 15) * 17 for s in (8, 4, 0, 12)))
        im = Image.new('RGBA', (32, 32))
        im.putdata([cols[(bmp[i // 2] >> (0 if i % 2 else 4)) & 15] for i in range(1024)])
        sheet.alpha_composite(im.resize((96, 96), Image.NEAREST), (8 + k * 104, 4))
    sheet.save(out / 'icons.png')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
