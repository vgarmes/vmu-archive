"""Pull Guilty Gear X's VMU screen out of its program, and its save icons out
of /VMICON01.ICO to /VMICON03.ICO.

    python3 vmu.py <folder with 1ST_READ.BIN and VMICON0*.ICO> <out dir>

Writes <out>/inbox/ (the screen as a PNG, dark = lit, with its sidecar, for
`pnpm icons:import`), <out>/saves/<icon>/ (a save header rebuilt as the game
writes it, with a save-icons.json, for `pnpm saveicons:import`, one folder an
icon so each entry names its own file) for every icon the archive lacks, and
<out>/contact-sheet.png.

Redump `Guilty Gear X (Japan)` (T-2402M V2.000); 1ST_READ.BIN loads at
0x8C010000. Before writing anything it checks, in the program, the facts the
entries rest on. See content/games/guilty-gear-x.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
REPO = Path(__file__).resolve().parents[3]
W, H = 48, 32
BASE = dict(game='guilty-gear-x', publisher='Sammy', year=2000, region='ntsc-j')

# pdLcd 1.04's write, found by its bytes (the same build as Resident Evil 3's),
# is loaded in one place, 0x8C081384, which sends the one screen at SCREEN: a
# byte a dot, 8 lit and 0 not, stored as shown. The flag beside it only turns
# it for a VMU that reports another orientation.
LCD_WRITE, CALL, SCREEN = 0x8C0C6738, 0x8C081384, 0x8C0AA25E

# The save's icon and VMU name, picked by the unlock byte at 0x8C0EFB51 (0-3)
# from a table of 36-byte entries: the icon's file name (16 bytes), its frame
# count and animation speed (two 16-bit words), and the VMU name (16 bytes).
# The save's description, the same for all, is DESCRIPTION.
TABLE, ENTRIES = 0x8C0AA85E, 4
DESCRIPTION = 0x8C0AA94C
TITLES = {  # by the unlock level that picks the entry
    0: 'Save file (nothing unlocked)',
    1: 'Save file (Testament unlocked)',
    2: 'Save file (Dizzy unlocked)',  # also level 3, GG mode
}


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def literal_loads(b, value):
    """Addresses of `mov.l @(disp,pc),Rn` instructions loading value."""
    out = []
    for off in range(0, len(b) - 1, 2):
        w = b[off] | b[off + 1] << 8
        if w >> 12 == 0xD:
            lit = (off & ~3) + 4 + (w & 0xFF) * 4
            if lit + 4 <= len(b) and struct.unpack_from('<I', b, lit)[0] == value:
                out.append(LOAD + off)
    return out


def sjis(raw):
    return raw.split(b'\0')[0].decode('shift_jis')


def palette(raw):
    out = []
    for i in range(16):
        v = int.from_bytes(raw[2 * i:2 * i + 2], 'little')
        a, r, g, bl = (v >> 12) & 15, (v >> 8) & 15, (v >> 4) & 15, v & 15
        out.append('#' + ''.join(f'{n * 17:02x}' for n in (r, g, bl, a)))
    return out


def main(src, out):
    src, out = Path(src), Path(out)
    b = (src / '1ST_READ.BIN').read_bytes()

    assert literal_loads(b, LCD_WRITE) == [CALL], literal_loads(b, LCD_WRITE)
    assert literal_loads(b, SCREEN) == [CALL + 2]
    raw = at(b, SCREEN, W * H)
    assert set(raw) == {0, 8}
    assert at(b, SCREEN + W * H, 12) == b'VMICON01.ICO'  # nothing more follows it

    inbox = out / 'inbox'
    shutil.rmtree(inbox, ignore_errors=True)
    inbox.mkdir(parents=True)
    screen = Image.new('1', (W, H), 1)
    screen.putdata([0 if v else 1 for v in raw])
    screen.save(inbox / 'guilty-gear-x-logo.png')
    (inbox / 'guilty-gear-x-logo.json').write_text(
        json.dumps(dict(title='Guilty Gear X logo', **BASE, tags=['logo']), ensure_ascii=False, indent=1) + '\n')

    description = sjis(at(b, DESCRIPTION, 32))
    have = {}
    for path in (REPO / 'content/save-icons/guilty-gear-x').glob('*.json'):
        s = json.loads(path.read_text())
        have[(tuple(s['palette']), tuple(s['frames']))] = path.name
    shutil.rmtree(out / 'saves', ignore_errors=True)
    seen, icons = set(), []
    for k in range(ENTRIES):
        e = at(b, TABLE + 36 * k, 36)
        name = sjis(e[:16])
        count, speed = struct.unpack('<HH', e[16:20])
        vmu_name = sjis(e[20:36])
        print(f'unlock {k}: /{name}, {count} frames, speed {speed}, {vmu_name}')
        if name in seen:
            continue
        seen.add(name)
        ico = (src / name).read_bytes()
        assert len(ico) == 0x20 + count * 0x200
        frames = [ico[0x20 + n * 0x200:0x20 + (n + 1) * 0x200] for n in range(count)]
        icons.append((name, ico))
        hit = have.get((tuple(palette(ico[:0x20])), tuple(f.hex() for f in frames)))
        if hit:
            print(f'  is the archive\'s {hit}')
            continue
        hdr = bytearray(0x80)
        hdr[0:16] = vmu_name.encode('shift_jis').ljust(16, b' ')
        hdr[0x10:0x30] = description.encode('shift_jis').ljust(32, b' ')
        struct.pack_into('<HH', hdr, 0x40, count, speed)
        hdr[0x60:0x80] = ico[:0x20]
        folder = out / 'saves' / name.split('.')[0]
        folder.mkdir(parents=True)
        (folder / 'DCGUILTY.VMS').write_bytes(bytes(hdr) + b''.join(frames))
        (folder / 'save-icons.json').write_text(json.dumps(dict(
            **BASE, disc=f'/{name}', titles={'DCGUILTY.VMS': TITLES[k]}), ensure_ascii=False, indent=1) + '\n')
        print(f'  new: {TITLES[k]} -> {folder}')

    scale = 4
    sheet = Image.new('RGB', (16 + W * scale + 16 + len(icons) * (2 * 32 * scale + 24), 40 + 32 * scale + 16), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), f'Guilty Gear X: the screen @ {SCREEN:#x}, then /VMICON0*.ICO', fill='black')
    sheet.paste(screen.convert('RGB').resize((W * scale, H * scale), Image.NEAREST), (16, 40))
    x = 32 + W * scale
    for name, ico in icons:
        pal = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in palette(ico[:0x20])]
        for n in range((len(ico) - 0x20) // 0x200):
            f = ico[0x20 + n * 0x200:0x20 + (n + 1) * 0x200]
            im = Image.new('RGB', (32, 32))
            im.putdata([pal[f[p // 2] >> 4 if p % 2 == 0 else f[p // 2] & 15] for p in range(1024)])
            sheet.paste(im.resize((32 * scale, 32 * scale), Image.NEAREST), (x, 40))
            x += 32 * scale + 4
        x += 20
    sheet.save(out / 'contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
