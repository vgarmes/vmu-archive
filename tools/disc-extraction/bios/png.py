"""Write 1-bit art as PNGs without Pillow: dark = lit, as `pnpm icons:import` reads it."""
import struct
import zlib


def bits(data, w, h, row_bytes=None):
    """Rows of 0/1 from packed 1bpp data, high bit first, 1 = lit."""
    rb = row_bytes or (w + 7) // 8
    return [[data[y * rb + x // 8] >> (7 - x % 8) & 1 for x in range(w)] for y in range(h)]


def blank(w, h):
    return [[0] * w for _ in range(h)]


def paste(dst, src, x0, y0):
    for y, row in enumerate(src):
        dst[y0 + y][x0:x0 + len(row)] = row


def save(path, px, scale=1, gap=None):
    """Grey 0 for lit, 255 for unlit; `gap` (a value) marks cells that are neither."""
    h, w = len(px), len(px[0])
    raw = bytearray()
    for y in range(h * scale):
        raw.append(0)
        for x in range(w * scale):
            v = px[y // scale][x // scale]
            raw.append(gap if v is None else (0 if v else 255))
    def chunk(t, c):
        return struct.pack('>I', len(c)) + t + c + struct.pack('>I', zlib.crc32(t + c) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n'
                + chunk(b'IHDR', struct.pack('>IIBBBBB', w * scale, h * scale, 8, 0, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b''))


def sheet(images, cols, pad=2):
    """Equal-size images in a grid with grey gutters, for contact sheets."""
    h, w = len(images[0]), len(images[0][0])
    rows = (len(images) + cols - 1) // cols
    out = [[None] * (pad + cols * (w + pad)) for _ in range(pad + rows * (h + pad))]
    for i, im in enumerate(images):
        paste(out, im, pad + (i % cols) * (w + pad), pad + (i // cols) * (h + pad))
    return out
