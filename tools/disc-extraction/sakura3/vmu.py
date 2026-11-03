"""Decode Sakura Taisen 3's VMU art (LCD1 blocks) from files copied off disc 1.

    python3 vmu.py <files dir> <out dir>

<files dir> holds the files as disc.py copies them (ADVDATA/SYSTEM.LC1,
MINIGAME/...). Every LCD1 block in those files is decoded:

    "LCD1", u32 size, u32 table offset, u32 count     (offsets count from +8)
    table: count × { u32 data offset, u16 height, u16 width, u32 flag,
                     u32 data size, u32 0 }
    data: nibble run-length bytes, high nibble = run, low nibble = value

The loader is at 0x8C15EC3C in 1ST_READ.BIN, the decoder at 0x8C15ECC0. An entry
unpacks to height x width bytes, one per pixel: a 48-wide strip of frames side by
side. Each value is a brightness, 0 (dark) to 15 (light). A Flycast capture of
the logo (SYSTEM.LC1 entry 4, frame 10) matches with a dot lit wherever the
value is below 8: 0 and 7 are lit, 15 is unlit. Value 8 (only in SYSTEM.LC1
entry 3) is unlit by that rule but no capture covers it yet.

Writes lcd/<source>-<entry>.png (frames stacked top to bottom; dark = lit, grey
kept as grey), manifest.json and contact-sheet.png.
"""
import collections
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SOURCES = [
    'ADVDATA/SYSTEM.LC1',
    *[f'MINIGAME/{n}' for n in (
        'KAJINO1.LC1', 'KAJINO2.LC1', 'KAJINO3.LC1', 'MGBJ.BIN', 'MGERK.BIN', 'MGGRI.BIN',
        'MGHAN.BIN', 'MGKG_COQ.LC1', 'MGKG_ERI.LC1', 'MGKG_GLY.LC1', 'MGKG_HAN.LC1',
        'MGKG_OGA.LC1', 'MGKG_ROB.LC1', 'MGKOK.BIN', 'MGKT.BIN', 'MGPOK.BIN', 'MGROB.BIN',
        'MGRU.BIN', 'MGSLOT.BIN')],
    # Battle units: special attack names and boss names, scrolled across the VMU.
    *[f'SLG/UNITS/{n}_N.BC' for n in (
        'BOSS_CROW', 'BOSS_LION', 'BOSS_RABBIT', 'BOSS_SCORPION', 'BOSS_SNAKE',
        'COQUELICOT_F1', 'ERICA_F1', 'GLYCINE_F1', 'HANABI_F1', 'LOBELIA_F1',
        'OGAMI_F1A', 'OGAMI_F1B', 'OGAMI_F1C')],
]
FW, FH = 48, 32


def lcd1(b, base):
    table, count = struct.unpack_from('<II', b, base + 8)
    for k in range(count):
        off, h, w, flag, size, _ = struct.unpack_from('<IHHIII', b, base + 8 + table + k * 20)
        px = bytearray()
        for x in b[base + 8 + off:base + 8 + off + size]:
            px += bytes([x & 15]) * (x >> 4)
        assert len(px) == h * w, f'entry {k}: {len(px)} bytes for {w}x{h}'
        yield k, w, h, bytes(px)


def frames(w, h, px):
    """Split a strip into 48x32 frames, each a list of rows of values."""
    rows = [px[r * w:(r + 1) * w] for r in range(h)]
    return [[row[f * FW:(f + 1) * FW] for row in rows] for f in range(w // FW)]


def lit(v):
    """Checked against a Flycast capture: values below 8 show as a lit dot."""
    return v < 8


def frame_hex(frame):
    bits = ''.join('1' if lit(v) else '0' for row in frame for v in row)
    return ''.join(f'{int(bits[i:i + 8], 2):02x}' for i in range(0, len(bits), 8))


def main(files, out):
    files, out = Path(files), Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for src in SOURCES:
        b = (files / src).read_bytes()
        base = b.find(b'LCD1')
        assert base >= 0, f'no LCD1 block in {src}'
        stem = Path(src).stem.lower()
        for k, w, h, px in lcd1(b, base):
            name = f'{stem}-{k:02d}'
            values = sorted(set(px))
            # A unit's entries are banners the game scrolls, even when 48 divides
            # their width (Royal rage is 144 px); never split them into frames.
            screen = h == FH and w % FW == 0 and not src.startswith('SLG/UNITS/')
            fs = frames(w, h, px) if screen else []
            im = Image.new('L', (FW, FH * len(fs)) if screen else (w, h), 255)
            if screen:
                im.putdata([v * 17 for f in fs for row in f for v in row])
            else:
                im.putdata([v * 17 for v in px])
            im.save(out / 'lcd' / f'{name}.png')
            manifest.append(dict(
                name=name, source=src, entry=k, width=w, height=h, frames=len(fs), values=values,
                grey=any(v not in (0, 15) for v in values), unverified=8 in values,
                frame_hex=[frame_hex(f) for f in fs] if screen else None))
            images.append((name, im))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    counts = collections.Counter(
        'grey' if m['grey'] else 'strip' if m['frames'] > 1 else 'still' for m in manifest)
    scale, cols = 2, 12
    cw, ch = FW * scale + 10, FH * scale + 24
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new('RGB', (10 + cols * cw, 30 + rows * ch), '#f5f2e9')
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), f'{len(manifest)} entries: {dict(counts)}', fill='black')
    for n, (name, im) in enumerate(images):
        x, y = 10 + n % cols * cw, 30 + n // cols * ch
        d.text((x, y), name, fill='black')
        first = im.crop((0, 0, FW, FH))
        sheet.paste(first.convert('RGB').resize((FW * scale, FH * scale), Image.NEAREST), (x, y + 12))
    sheet.save(out / 'contact-sheet.png')
    print(len(manifest), 'entries:', dict(counts), '->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
