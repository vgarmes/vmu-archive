"""Pull Grandia II's four VMU screens out of its program.

    python3 vmu.py <jp|eu> <folder with 1ST_READ.BIN, BIN/GR2TITLE.BIN, BIN/FIELD.BIN> <out dir>

Writes <out>/inbox/ (each screen as a PNG, dark = lit, with its sidecar, for
`pnpm icons:import`) and <out>/contact-sheet.png.

Redump `Grandia II (Japan)` (jp) and `Grandia II (Europe)` (eu); in both,
1ST_READ.BIN loads at 0x8C010000, and the title and field overlays,
GR2TITLE.BIN and FIELD.BIN, at 0x8C380000. Before writing anything it checks,
in the program and the overlays, the facts the entries rest on. See
content/games/grandia-2.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD, OVERLAY = 0x8C010000, 0x8C380000
W, H = 48, 32
SIZE = W * H // 8
BASE = dict(game='grandia-2', publisher='Game Arts', year=2000)

# The game's send (0x8C010B3E) takes a list of packed screens and sends
# screen number `frame` to every VMU that has a screen, when it changes, with
# pdLcd 1.04's write for packed screens (`packed`), after the library's check
# that a VMU with a screen is there (`check`). Its one caller, 0x8C01051E,
# hands it `screens`. The library's write that turns a screen for the VMU's
# orientation (`write`) is linked but never called. Start-up (0x8C010080)
# copies `vmu_table` (reset to the logo, then send) to 0x8CFFDE00 and
# `var_table` to 0x8CFFF000, whose fifth word points at `frame`; the overlays
# use those. `lcd_table` is the library's own table of its routines, which
# start-up copies to 0x8CFFB6B8, where no overlay reads it.
SEND, SEND_CALLER, RESET = 0x8C010B3E, 0x8C01051E, 0x8C0104CA
VMU_SLOT, VAR_SLOT = 0x8CFFDE00, 0x8CFFF000
FRAME_SLOT = VAR_SLOT + 0x10
HOLD_AT = {'jp': 120, 'eu': 15}

RELEASES = {
    'jp': dict(
        packed=0x8C03864E, write=0x8C0385E8, check=0x8C038698, lcd_table=0x8C01AF58,
        screens=0x8C019588, frame=0x8C1484E8, vmu_table=0x8C01B540, var_table=0x8C01B520,
        build=b'pdLcd Ver 1.04 Build:Apr 26 1999 16:55:25',
        # Where each overlay's memory card code picks a screen (the `mov #n`
        # and n: Accessing, then OK or NG) and holds OK or NG until its count
        # reaches HOLD_AT.
        picks={
            'BIN/GR2TITLE.BIN': ([(0x8C3817F6, 3), (0x8C38180E, 2), (0x8C381818, 1)], 0x8C38183E),
            'BIN/FIELD.BIN': ([(0x8C3D3D7E, 3), (0x8C3D3D96, 2), (0x8C3D3DA0, 1)], 0x8C3D3DC6),
        },
        screens_meta=[
            ('grandia-2-logo', 'Grandia II logo', ['logo'], 'ntsc-j'),
            ('grandia-2-ng', 'NG', ['memory-card'], None),
            ('grandia-2-ok', 'OK', ['memory-card'], None),
            ('grandia-2-accessing', 'Accessing', ['memory-card'], 'ntsc-j'),
        ],
    ),
    'eu': dict(
        packed=0x8C03866E, write=0x8C038608, check=0x8C0386B8, lcd_table=0x8C01AF78,
        screens=0x8C0195A8, frame=0x8C148508, vmu_table=0x8C01B560, var_table=0x8C01B540,
        build=b'pdLcd Ver 1.04 Build:Apr 26 1999 16:55:25',
        picks={
            'BIN/GR2TITLE.BIN': ([(0x8C38181E, 3), (0x8C381836, 2), (0x8C381840, 1)], 0x8C381882),
            'BIN/FIELD.BIN': ([(0x8C3D5080, 3), (0x8C3D5098, 2), (0x8C3D50A2, 1)], 0x8C3D50FE),
        },
        # NG and OK are the Japanese disc's, byte for byte; the importer
        # skips them as duplicates.
        screens_meta=[
            ('grandia-2-logo', 'Grandia II logo', ['logo'], None),
            ('grandia-2-ng', 'NG', ['memory-card'], None),
            ('grandia-2-ok', 'OK', ['memory-card'], None),
            ('grandia-2-accessing', 'Accessing', ['memory-card'], None),
        ],
    ),
}


def at(b, addr, n, load=LOAD):
    return b[addr - load:addr - load + n]


def word(b, addr, load=LOAD):
    return struct.unpack('<I', at(b, addr, 4, load))[0]


def literal_loads(b, value, load=LOAD):
    """Addresses of `mov.l @(disp,pc),Rn` instructions loading value."""
    out = []
    for off in range(0, len(b) - 1, 2):
        w = b[off] | b[off + 1] << 8
        if w >> 12 == 0xD:
            lit = (off & ~3) + 4 + (w & 0xFF) * 4
            if lit + 4 <= len(b) and struct.unpack_from('<I', b, lit)[0] == value:
                out.append(load + off)
    return out


def mov_imm(b, addr, load):
    """The value of the `mov #imm,Rn` at addr."""
    w = struct.unpack('<H', at(b, addr, 2, load))[0]
    assert w >> 12 == 0xE, hex(addr)
    return w & 0xFF


def main(release, src, out):
    r = RELEASES[release]
    src, out = Path(src), Path(out)
    b = (src / '1ST_READ.BIN').read_bytes()

    assert r['build'] in b
    # The send is the only code that loads the library's writes.
    assert literal_loads(b, r['packed']) == [0x8C010B5A]
    assert literal_loads(b, r['check']) == [0x8C010B76, 0x8C010C10]
    assert literal_loads(b, r['write']) == []
    assert [word(b, r['lcd_table'] + 4 * k) for k in range(3)] == [r['check'], r['write'], r['packed']]
    assert literal_loads(b, SEND) == [SEND_CALLER]
    assert literal_loads(b, r['screens']) == [SEND_CALLER + 2]
    assert literal_loads(b, r['frame']) == [0x8C01090C, 0x8C010B50]  # the reset sets it to 0
    for frm, to in ((r['vmu_table'], VMU_SLOT), (r['var_table'], VAR_SLOT)):
        assert any(word(b, a) == frm and word(b, a + 4) == to for a in range(0x8C010100, 0x8C0101C0, 4)), hex(frm)
    assert word(b, r['vmu_table']) == RESET and word(b, r['vmu_table'] + 4) == SEND_CALLER
    assert word(b, r['var_table'] + FRAME_SLOT - VAR_SLOT) == r['frame']
    # Four screens, then not a fifth: 24 empty bytes and a table of pointers.
    assert at(b, r['screens'] + 4 * SIZE, 24) == bytes(24)
    assert word(b, r['screens'] + 4 * SIZE + 24) >> 24 == 0x8C

    for name, (picks, hold) in r['picks'].items():
        o = (src / name).read_bytes()
        assert literal_loads(o, FRAME_SLOT, OVERLAY), name
        for addr, n in picks:
            assert mov_imm(o, addr, OVERLAY) == n, (name, hex(addr))
        assert mov_imm(o, hold, OVERLAY) == HOLD_AT[release], name

    inbox = out / 'inbox'
    shutil.rmtree(inbox, ignore_errors=True)
    inbox.mkdir(parents=True)
    screens = []
    for k, (slug, title, tags, region) in enumerate(r['screens_meta']):
        raw = at(b, r['screens'] + k * SIZE, SIZE)
        im = Image.new('1', (W, H), 1)
        im.putdata([0 if raw[i // 8] >> (7 - i % 8) & 1 else 1 for i in range(W * H)])
        im = im.rotate(180)  # stored as the LCD takes it
        im.save(inbox / f'{slug}.png')
        meta = dict(title=title, **BASE, tags=tags)
        if region:
            meta['region'] = region
        (inbox / f'{slug}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n')
        screens.append((f'{k}: {title}', im))
        print(f'screen {k} at {r["screens"] + k * SIZE:#x} -> {slug}')

    scale = 4
    sheet = Image.new('RGB', (16 + len(screens) * (W * scale + 16), 40 + H * scale + 32), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), f'Grandia II ({release}): 1ST_READ.BIN {r["screens"]:#x}', fill='black')
    for k, (label, im) in enumerate(screens):
        x = 16 + k * (W * scale + 16)
        sheet.paste(im.convert('RGB').resize((W * scale, H * scale), Image.NEAREST), (x, 40))
        draw.text((x, 44 + H * scale), label, fill='black')
    sheet.save(out / 'contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] not in RELEASES:
        sys.exit(__doc__)
    main(*sys.argv[1:])
