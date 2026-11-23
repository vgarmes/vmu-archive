"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per screen or sprite, screens in <inbox>/screens
and the font in <inbox>/sprites.
"""
import json
import shutil
import sys
from pathlib import Path

# Released in Japan alone.
BASE = dict(game='Napple Tale: Arsia in Daydream', publisher='Sega', year=2000, region='ntsc-j')
META = {
    '00': dict(title='Napple Tale logo', tags=['logo']),
    '01': dict(title='Saving', tags=['status']),
    '02': dict(title='Loading', tags=['status']),
    '03': dict(title='OK', tags=['status']),
    '04': dict(title='Failed', tags=['status']),
    '05': dict(title='In use', tags=['status']),
    'font': dict(title='Score display font', tags=['font'], sprite=True,
                 glyphs=dict(height=6, width=4),
                 source=dict(file='/1ST_READ.BIN', offset=0x8C0FEADC - 0x8C010000)),
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    for kind in ('screens', 'sprites'):
        (inbox / kind).mkdir(parents=True)
    manifest = json.loads((out / 'manifest.json').read_text())
    for m in manifest:
        meta = META[m['name']]
        stem = f'napple-tale-{m["name"]}-' + meta['title'].lower().replace(' ', '-')
        dest = inbox / m['kind']
        shutil.copy(out / m['kind'] / f'{m["name"]}.png', dest / f'{stem}.png')
        (dest / f'{stem}.json').write_text(json.dumps(dict(**meta, **BASE), ensure_ascii=False, indent=1))
    print(len(manifest), 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
