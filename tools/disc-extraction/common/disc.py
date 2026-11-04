"""Read files from a Dreamcast GD-ROM dump: a folder with a .gdi or a Redump .cue, and its tracks.

    python3 disc.py <dump folder> <inventory.json>    list every file on the disc
    python3 disc.py <dump folder> <out dir> <path>…   copy files off the disc

Adapted from the Shenmue VMU extraction's inspect_discs.py. Only data tracks are
read; the filesystem is the ISO 9660 volume in the high-density area (LBA 45000+).
"""
import json
import shlex
import struct
import sys
from pathlib import Path


class Disc:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.tracks = []
        gdi = next(self.folder.glob('*.gdi'), None)
        if gdi is None:
            self.read_cue(next(self.folder.glob('*.cue')))
            return
        for line in gdi.read_text().splitlines()[1:]:
            if not line.strip():
                continue
            _, lba, kind, sector, name, offset = shlex.split(line)
            if kind == '4':  # data track
                self.tracks.append((int(lba), int(sector), int(offset), (self.folder / name).open('rb')))

    def read_cue(self, cue):
        # Redump splits a GD-ROM into a single-density area (tracks 1 and 2)
        # and a high-density area from LBA 45000, each track a raw 2352-byte
        # .bin. Tracks in an area run back to back.
        lba = 0
        name = None
        for line in cue.read_text().splitlines():
            words = shlex.split(line)
            if not words:
                continue
            if line.strip() == 'REM HIGH-DENSITY AREA':
                lba = 45000
            elif words[0] == 'FILE':
                name = words[1]
            elif words[0] == 'TRACK':
                path = self.folder / name
                if words[2].startswith('MODE1'):
                    self.tracks.append((lba, 2352, 0, path.open('rb')))
                lba += path.stat().st_size // 2352

    def read(self, lba, size):
        out = bytearray()
        while len(out) < size:
            start, sector, offset, f = max((t for t in self.tracks if t[0] <= lba), key=lambda t: t[0])
            # Raw 2352-byte sectors carry a 16-byte header before the 2048 bytes of data.
            f.seek(offset + (lba - start) * sector + (16 if sector == 2352 else 0))
            out += f.read(2048)
            lba += 1
        return bytes(out[:size])

    def files(self):
        pvd = self.read(45016, 2048)  # primary volume descriptor of the high-density area
        assert pvd[1:6] == b'CD001', 'no ISO 9660 volume where a GD-ROM keeps it'

        def record(r):
            return struct.unpack_from('<I', r, 2)[0], struct.unpack_from('<I', r, 10)[0], r[25]

        found = []

        def walk(lba, size, path):
            data = self.read(lba, size)
            pos = 0
            while pos < len(data):
                n = data[pos]
                if not n:  # records never cross a sector: skip to the next one
                    pos = (pos // 2048 + 1) * 2048
                    continue
                r = data[pos:pos + n]
                pos += n
                name = r[33:33 + r[32]]
                if name in (b'\x00', b'\x01'):  # . and ..
                    continue
                name = name.decode('ascii', 'replace').split(';')[0]
                child_lba, child_size, flags = record(r)
                if flags & 2:
                    walk(child_lba, child_size, f'{path}/{name}')
                else:
                    found.append(dict(path=f'{path}/{name}', lba=child_lba, size=child_size))

        root_lba, root_size, _ = record(pvd[156:190])
        walk(root_lba, root_size, '')
        return found


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    disc = Disc(sys.argv[1])
    files = disc.files()
    if len(sys.argv) == 3:
        Path(sys.argv[2]).write_text(json.dumps(files, indent=1))
        print(len(files), 'files,', sum(f['size'] for f in files) // 2**20, 'MiB')
    else:
        by_path = {f['path']: f for f in files}
        for wanted in sys.argv[3:]:
            f = by_path[wanted]
            dest = Path(sys.argv[2]) / wanted.lstrip('/')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(disc.read(f['lba'], f['size']))
            print('wrote', dest, f['size'], 'bytes')
