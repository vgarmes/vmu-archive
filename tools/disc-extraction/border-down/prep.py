"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per screen or sprite, screens in <inbox>/screens
and sprites in <inbox>/sprites: import the screens first, since the digits
name the counter screen they're drawn on.
"""
import json
import shutil
import sys
from pathlib import Path

# Released in Japan alone.
BASE = dict(game='Border Down', publisher='G.rev', year=2003, region='ntsc-j')
META = {
    'logo': dict(title='SDF logo', tags=['logo']),
    'hit-counter': dict(title='Hit counter', tags=['status']),
    'digits': dict(title='Hit counter digits', tags=['font', 'digits'], sprite=True,
                   glyphs=dict(height=12, width=10),
                   source=dict(file='/1ST_READ.BIN', offset=0x8C1464D4 - 0x8C010000),
                   # the count of 0 on the counter screen: '0' at x 1 + 12 * 3
                   drawnAt=[dict(screen='border-down-hit-counter', x=37, y=10, glyph=0)]),
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    for kind in ('screens', 'sprites'):
        (inbox / kind).mkdir(parents=True)
    manifest = json.loads((out / 'manifest.json').read_text())
    for m in manifest:
        stem = f'border-down-{m["name"]}'
        dest = inbox / m['kind']
        shutil.copy(out / m['kind'] / f'{m["name"]}.png', dest / f'{stem}.png')
        meta = dict(**META[m['name']], **BASE)
        (dest / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(len(manifest), 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
