"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Reads every <release>.json in the out dir and writes one PNG and sidecar per
screen the archive doesn't have yet. No region: the Power Stone names and logos
are the same in every release.
"""
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
YEARS = {'Power Stone': 1999, 'Power Stone 2': 2000}
TITLES = {'title': ('Title screen', ['logo']), 'access': ('Access', ['logo', 'memory-card'])}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    have = set()
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['gameId'] in ('power-stone', 'power-stone-2'):
            have.update(data['frames'])
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for manifest in sorted(out.glob('ps*.json')):
        for m in json.loads(manifest.read_text()):
            if m['frame_hex'] in have:
                print('already in the archive:', m['game'], m['what'])
                continue
            title, tags = TITLES[m['what']]
            stem = f'power-stone-{m["name"]}'
            shutil.copy(out / 'lcd' / f'{m["name"]}.png', inbox / f'{stem}.png')
            meta = dict(title=title, game=m['game'], publisher='Capcom', year=YEARS[m['game']], tags=tags)
            (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
            written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
