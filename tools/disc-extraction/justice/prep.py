"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per screen the archive doesn't have yet.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

GAME = 'Project Justice'
GAME_ID = 'project-justice'  # its id in content/games.json
REPO = Path(__file__).resolve().parents[3]
BASE = dict(game=GAME, publisher='Capcom', year=2000)
# (title, tags, region). Region follows the logo, not the disc: the Japanese pair
# is JP; the Project Justice pair (the US and European title) gets none, since
# this Japanese disc carries it too.
TITLES = {
    0: ('Title screen', ['logo'], 'ntsc-j'),
    1: ('Access', ['logo', 'memory-card'], 'ntsc-j'),
    2: ('Title screen', ['logo'], None),
    3: ('Access', ['logo', 'memory-card'], None),
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    have = set()
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['gameId'] == GAME_ID:
            have.update(data['frames'])
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for m in json.loads((out / 'manifest.json').read_text()):
        n = int(m['name'])
        if m['frame_hex'] in have:
            print('already in the archive:', m['what'])
            continue
        title, tags, region = TITLES[n]
        stem = f'justice-{n:02d}'
        shutil.copy(out / 'lcd' / f'{n:02d}.png', inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, **({'region': region} if region else {}), tags=tags)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
