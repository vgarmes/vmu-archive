"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per screen.
"""
import json
import shutil
import sys
from pathlib import Path

# The Dreamcast release was Japan's alone (elsewhere Part 2 came out on PS2).
BASE = dict(game='Space Channel 5: Part 2', publisher='Sega', year=2002, region='ntsc-j')
META = {
    0: ('Channel 5 logo', ['logo']),
    1: ('Now loading', ['status']),
    2: ('Now saving', ['status']),
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    manifest = json.loads((out / 'manifest.json').read_text())
    for m in manifest:
        title, tags = META[m['entry']]
        stem = f'space-channel-5-part-2-{m["entry"]:02d}-' + title.lower().replace(' ', '-')
        shutil.copy(out / 'screens' / f'{m["name"]}.png', inbox / f'{stem}.png')
        (inbox / f'{stem}.json').write_text(json.dumps(dict(title=title, **BASE, tags=tags),
                                                       ensure_ascii=False, indent=1))
    print(len(manifest), 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
