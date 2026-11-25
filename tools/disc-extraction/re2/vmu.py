"""Pull Resident Evil 2's VMU screens, sprites and save icons out of /BIO2DC.EXE.

    python3 vmu.py <BIO2DC.EXE> <out dir>

Writes <out>/inbox/ (screens and sprites as PNGs, dark = lit, with sidecars,
for `pnpm icons:import`), <out>/saves/<icon>/ (a save rebuilt for each icon
the archive lacks, for `pnpm saveicons:import`, one folder an icon so each
entry names its own resource) and <out>/contact-sheet.png.

Redump `Resident Evil 2 (Europe) (En,Fr) (Disc 1)` (T-7004D-50 V1.000) and
`Biohazard 2 - Value Plus (Japan) (Disc 1)` (T-1214M V1.005); it tells the two
programs apart by their resources. The European one has the art in English
and French, the Japanese one once, in Japanese. The addresses below are the
European program's unless said. The game is a Windows CE program, not a 1ST_READ.BIN: BIO2DC.EXE is an SH-4 PE
file with image base 0x10000, and it reaches the VMU through MAPLEDEV.dll.
Addresses below are virtual addresses in that image. Its VMU art and save
icons are resources of type "BM" in .rsrc. Before writing anything it checks,
in the code, the facts the entries rest on. See content/games/resident-evil-2.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[3]
GAME = 'resident-evil-2'
BASE = dict(game=GAME, publisher='Capcom', year=1999)
W, H = 48, 32
ROW = 8  # a resource's row: 6 bytes of dots, then 2 of padding


# ---- the PE image -----------------------------------------------------------

def flat(b):
    """The EXE laid out from its image base: offset = virtual address - base."""
    pe = struct.unpack_from('<I', b, 0x3C)[0]
    assert b[pe:pe + 4] == b'PE\0\0' and struct.unpack_from('<H', b, pe + 4)[0] == 0x1A6, 'not an SH-4 PE'
    count, opt = struct.unpack_from('<HxxxxxxxxxxxxH', b, pe + 6)
    base, size = struct.unpack_from('<I', b, pe + 24 + 28)[0], struct.unpack_from('<I', b, pe + 24 + 56)[0]
    assert base == 0x10000
    img = bytearray(size)
    for i in range(count):
        _, vsize, rva, rsize, raw = struct.unpack_from('<8sIIII', b, pe + 24 + opt + 40 * i)
        n = min(rsize, vsize or rsize)
        img[rva:rva + n] = b[raw:raw + n]
    rsrc = struct.unpack_from('<I', b, pe + 24 + 96 + 8 * 2)[0]
    return bytes(img), rsrc


def resources(img, rsrc):
    """{name: bytes} for the "BM" resources."""
    out = {}

    def name(e):
        if e & 0x80000000:
            o = rsrc + (e & 0x7FFFFFFF)
            return img[o + 2:o + 2 + 2 * struct.unpack_from('<H', img, o)[0]].decode('utf-16le')
        return str(e)

    def walk(off, path):
        nn, ni = struct.unpack_from('<HH', img, rsrc + off + 12)
        for i in range(nn + ni):
            e, d = struct.unpack_from('<II', img, rsrc + off + 16 + 8 * i)
            p = path + [name(e)]
            if d & 0x80000000:
                walk(d & 0x7FFFFFFF, p)
            elif p[0] == 'BM':
                rva, size = struct.unpack_from('<II', img, rsrc + d)
                out[p[1]] = img[rva:rva + size]

    walk(0, [])
    return out


def va(img, addr, n):
    return img[addr - 0x10000:addr - 0x10000 + n]


def words(img, lo, hi):
    return struct.unpack(f'<{(hi - lo) // 2}H', va(img, lo, hi - lo))


# ---- what the code says -----------------------------------------------------

STEP_MS = 500

# Per release: where the status update (the European one at 0x11DE64, which
# runs every VMU slot) checks its 500 ms (mov #125,r3 / mov.l @r8,r2 /
# shll2 r3), where the digit lookup is (the European one at 0x11DD1C), the
# art's language sets (a resource suffix, a title suffix, an id suffix), and
# the region of what's only in that release. The Japanese program draws the
# same status screen from its one set: the same rows, offsets, blinking and
# no-weapon test, read from its code (0x11A874), with the AMMO band drawn
# after the condition instead of before, which changes nothing.
RELEASES = {
    # names: the save header's fixed VMU name and description start
    'Europe': dict(interval=0x11DE9E, digit=0x11DD1C, region=None, names=(0x19A1EC, 0x19A1FC),
                   langs=[('_ENG', '', ''), ('_FRA', ' (French)', '-french')]),
    'Japan': dict(interval=0x11A8AE, digit=0x11A7BC, region='ntsc-j', names=(0x194328, 0x194334),
                  langs=[('', ' (Japanese)', '-japanese')]),
}
PARTS = ['VSAVE', 'VCONDITIONS', 'VCONNECT', 'VWEAPONS']


def release(res):
    for name, r in RELEASES.items():
        want = {p + lang for p in PARTS for lang, _, _ in r['langs']} | {'VTITLE', 'VNUMBERS'}
        if want <= set(res):
            return name, r
    sys.exit('neither the European nor the Japanese program')


def check_code(img, r):
    w = words(img, r['interval'], r['interval'] + 6)
    assert w == (0xE37D, 0x6282, 0x4308), [hex(x) for x in w]  # mov #125,r3 / mov.l @r8,r2 / shll2 r3
    # n <= 5 -> 5-n; 6..11 -> 5-(n-6)+72; 12.. -> 5-(n-12)+144
    w = words(img, r['digit'], r['digit'] + 0x2C)
    assert (w[0], w[3], w[9], w[10], w[16]) == (0xE105, 0xE30B, 0xE248, 0x4200, 0x7548), [hex(x) for x in w]


def digit_offset(n):
    return 5 - n if n <= 5 else 5 - (n - 6) + 72 if n <= 11 else 5 - (n - 12) + 144


# ---- drawing ----------------------------------------------------------------

def sheet(raw):
    """A resource as an upright image: rows of 6 bytes (2 of padding after),
    each row mirrored, as the LCD takes it once the buffer is turned."""
    assert len(raw) % ROW == 2 and raw[-2:] == b'\0\0'
    h = len(raw) // ROW
    assert all(raw[r * ROW + 6:r * ROW + 8] == b'\0\0' for r in range(h))
    im = Image.new('1', (W, h), 1)
    im.putdata([0 if raw[y * ROW + (47 - x) // 8] >> (7 - (47 - x) % 8) & 1 else 1
                for y in range(h) for x in range(W)])
    return im


def unsheet(im):
    """Back to the resource's bytes, to check nothing was lost."""
    out = bytearray(im.height * ROW + 2)
    px = im.load()
    for y in range(im.height):
        for x in range(W):
            if not px[x, y]:
                s = 47 - x
                out[y * ROW + s // 8] |= 0x80 >> (s % 8)
    return bytes(out)


class Lcd:
    """The 192-byte buffer and 0x8C0C89CC's copy into it (VA 0xC89CC)."""

    def __init__(self):
        self.buf = bytearray(192)

    def blit(self, src, x, y, w, h, off):
        base = 6 * (31 - y) - x  # sic: right for full-width pieces only
        for r in range(h):
            for k in range(w):
                self.buf[base - 6 * r + k] = src[off + ROW * r + k]

    def image(self):
        """The buffer as the VMU shows it: turned 180 degrees."""
        im = Image.new('1', (W, H), 1)
        im.putdata([0 if self.buf[(31 - y) * 6 + (47 - x) // 8] >> (7 - (47 - x) % 8) & 1 else 1
                    for y in range(H) for x in range(W)])
        return im


NONE = 16       # VWEAPONS' last entry, the dashes shown with no weapon
DASH = 11       # VNUMBERS' "-"
CONDITIONS = [  # (title, label offset in VCONDITIONS, blinks)
    ('Fine', 0, False),
    ('Caution (high)', 72, False),
    ('Caution (low)', 72, True),
    ('Danger', 144, True),
    ('Poison', 216, True),
]


def status(res, lang, label, show):
    """0x11DE64's status screen, no weapon equipped."""
    lcd = Lcd()
    cond, weapons = res[f'VCONDITIONS{lang}'], res[f'VWEAPONS{lang}']
    lcd.blit(cond, 0, 12, 6, 9, 288)  # AMMO / MUN
    if show:
        lcd.blit(cond, 0, 22, 6, 9, label)
    lcd.blit(weapons, 0, 2, 6, 9, 72 * NONE)
    for x in (5, 4, 3):
        lcd.blit(res['VNUMBERS'], x, 11, 1, 9, digit_offset(DASH))
    return lcd.image()


def full(res, name):
    lcd = Lcd()
    lcd.blit(res[name], 0, 0, 6, 32, 0)
    return lcd.image()


# ---- save icons -------------------------------------------------------------

def bmp_icon(raw):
    """A 4-bit 32x32 BMP resource: (ARGB4444 palette bytes, frame bytes)."""
    assert raw[:2] == b'BM'
    off = struct.unpack_from('<I', raw, 10)[0]
    w, h, _, bpp = struct.unpack_from('<iiHH', raw, 18)
    assert (w, h, bpp) == (32, 32, 4)
    ncol = struct.unpack_from('<I', raw, 46)[0] or 16
    # Always 16 entries from the palette's start, as the game reads it: a BMP
    # with fewer colours (SYSICON has 13) gives its first pixel bytes as the
    # rest, which is what dumped saves hold.
    pal = b''
    for i in range(16):
        bl, g, r = raw[54 + 4 * i:57 + 4 * i]
        pal += (0xF000 | (r >> 4) << 8 | (g >> 4) << 4 | bl >> 4).to_bytes(2, 'little')
    rows = [raw[off + 16 * r:off + 16 * (r + 1)] for r in range(32)]
    return pal, b''.join(reversed(rows)), ncol


def hex_palette(pal):
    out = []
    for i in range(16):
        v = int.from_bytes(pal[2 * i:2 * i + 2], 'little')
        out.append('#' + ''.join(f'{n * 17:02x}' for n in ((v >> 8) & 15, (v >> 4) & 15, v & 15, v >> 12)))
    return out


ICONS = ['ORLN', 'ORLU', 'ORCN', 'ORCU', 'ARLN', 'ARLU', 'ARCN', 'ARCU',
         'EXLEON', 'EXCLAIRE', 'EXADA', 'EXCHRIS', 'SYSICON']
SPEED = 15  # as every dumped save in the archive has it


# ---- main -------------------------------------------------------------------

def main(exe, out):
    out = Path(out)
    img, rsrc = flat(Path(exe).read_bytes())
    res = resources(img, rsrc)
    rel, r = release(res)
    check_code(img, r)
    region = dict(region=r['region']) if r['region'] else {}
    print(rel, 'program')

    inbox = out / 'inbox'
    shutil.rmtree(inbox, ignore_errors=True)
    inbox.mkdir(parents=True)

    def put(stem, frames, meta):
        strip = Image.new('1', (frames[0].width, sum(f.height for f in frames)), 1)
        y = 0
        for f in frames:
            strip.paste(f, (0, y))
            y += f.height
        strip.save(inbox / f'{GAME}-{stem}.png')
        (inbox / f'{GAME}-{stem}.json').write_text(
            json.dumps(dict(**meta, **BASE, **region), ensure_ascii=False, indent=1) + '\n')
        return frames

    # Pieces the same as the other release's are left for the importer to
    # skip as duplicates (Japan's ACCESS, CONNECT and digits are Europe's).
    shown = []
    title_slug = '' if rel == 'Europe' else '-japanese'
    shown += put(f'title-screen{title_slug}', [full(res, 'VTITLE')], dict(title='Title screen', tags=['logo']))
    for lang, suffix, slug in r['langs']:
        shown += put(f'access{slug}', [full(res, f'VSAVE{lang}')], dict(title=f'Access{suffix}', tags=['memory-card']))
        shown += put(f'connect{slug}', [full(res, f'VCONNECT{lang}')], dict(title=f'Connect{suffix}', tags=[]))
        for name, label, blinks in CONDITIONS:
            frames = [status(res, lang, label, True)] + ([status(res, lang, label, False)] if blinks else [])
            meta = dict(title=f'Condition: {name}{suffix}', tags=['status'])
            if blinks:
                meta['frameDelayMs'] = STEP_MS
            stem = 'condition-' + name.lower().replace(' (', '-').replace(')', '') + slug
            shown += put(stem, frames, meta)

    # the parts, kept whole as sprites, upright, after checking they give back
    # the resource's bytes
    for lang, suffix, slug in r['langs']:
        for key, title, count in (('VCONDITIONS', 'Condition labels', 5), ('VWEAPONS', 'Weapon names', 17)):
            raw = res[f'{key}{lang}']
            im = sheet(raw)
            assert unsheet(im) == raw and im.height == 9 * count
            put(f'{title.lower().replace(" ", "-")}{slug}', [im], dict(
                title=f'{title}{suffix}', sprite=True, glyphs=dict(height=9), tags=['status'],
                source=dict(file='/BIO2DC.EXE', entry=f'{key}{lang}')))

    # the digits: 6 cells of 8x9 a row, the game's 0-9 % - then the two halves
    # of the infinity sign; the four cells after it are empty
    raw = res['VNUMBERS']
    nums = sheet(raw)
    assert unsheet(nums) == raw and nums.height == 27
    font = Image.new('1', (8, 14 * 9), 1)
    for n in range(18):
        cell = nums.crop((8 * (n % 6), 9 * (n // 6), 8 * (n % 6) + 8, 9 * (n // 6) + 9))
        if n < 14:
            font.paste(cell, (0, 9 * n))
        else:
            assert cell.getextrema() == (1, 1), f'cell {n} is not empty'
    back = Image.new('1', (W, 27), 1)
    for n in range(14):
        back.paste(font.crop((0, 9 * n, 8, 9 * n + 9)), (8 * (n % 6), 9 * (n // 6)))
    assert unsheet(back) == raw
    for n in range(14):  # the game's index n is the byte the digit lookup gives it
        assert digit_offset(n) == 72 * (n // 6) + 5 - n % 6
    put('ammo-digits', [font], dict(
        title='Ammo digits', sprite=True, glyphs=dict(height=9), tags=['font', 'digits'],
        source=dict(file='/BIO2DC.EXE', entry='VNUMBERS')))

    # save icons
    have = {}
    for path in (REPO / 'content/save-icons' / GAME).glob('*.json'):
        s = json.loads(path.read_text())
        have[(tuple(s['palette']), tuple(s['frames']))] = path.name
    shutil.rmtree(out / 'saves', ignore_errors=True)
    vmu_name, description = (va(img, a, 16).split(b'\0')[0].decode('shift_jis') for a in r['names'])
    icons = []
    for name in ICONS:
        pal, frame, ncol = bmp_icon(res[name])
        icons.append((name, pal, frame))
        hit = have.get((tuple(hex_palette(pal)), (frame.hex(),)))
        print(f'{name}: {ncol} colours,', f'the archive\'s {hit}' if hit else 'new')
        if hit:
            continue
        hdr = bytearray(0x80)
        hdr[0:16] = vmu_name.encode('shift_jis').ljust(16, b' ')
        hdr[0x10:0x30] = description.encode('shift_jis').ljust(32, b' ')
        struct.pack_into('<HH', hdr, 0x40, 1, SPEED)
        hdr[0x60:0x80] = pal
        folder = out / 'saves' / name
        folder.mkdir(parents=True)
        (folder / f'{name}.VMS').write_bytes(bytes(hdr) + frame)
        (folder / 'save-icons.json').write_text(json.dumps(dict(
            **BASE, disc='/BIO2DC.EXE', titles={f'{name}.VMS': 'Save file'}), indent=1) + '\n')

    scale, cols = 3, 6
    cw, ch = W * scale + 12, H * scale + 12
    rows_ = (len(shown) + cols - 1) // cols
    sheet_ = Image.new('RGB', (12 + cols * cw, 40 + rows_ * ch + 32 * scale + 24), '#f5f2e9')
    draw = ImageDraw.Draw(sheet_)
    draw.text((12, 12), f'Resident Evil 2 ({rel}): /BIO2DC.EXE resources, every frame', fill='black')
    for n, im in enumerate(shown):
        sheet_.paste(im.convert('RGB').resize((W * scale, H * scale), Image.NEAREST),
                     (12 + n % cols * cw, 40 + n // cols * ch))
    y = 40 + rows_ * ch + 12
    for n, (name, pal, frame) in enumerate(icons):
        p = hex_palette(pal)
        colours = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in p]
        im = Image.new('RGB', (32, 32))
        im.putdata([colours[frame[i // 2] >> 4 if i % 2 == 0 else frame[i // 2] & 15] for i in range(1024)])
        sheet_.paste(im.resize((32 * 2, 32 * 2), Image.NEAREST), (12 + n * 70, y))
    sheet_.save(out / 'contact-sheet.png')
    print(len(shown), 'frames,', len(list(inbox.glob('*.json'))), 'entries ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
