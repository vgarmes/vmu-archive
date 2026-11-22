"""Turn vmu.py's screens into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per screen the archive doesn't have yet.
"""
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GAME_ID = 'super-puzzle-fighter-ii-x-for-matching-service'  # its id in content/games.json
# Released in Japan alone.
BASE = dict(game='Super Puzzle Fighter II X for Matching Service', publisher='Capcom',
            year=2001, region='ntsc-j')
SCREENS = {
    'title': dict(title='Title screen', tags=['logo']),
    'access': dict(title='Access', tags=['memory-card']),
    'ok': dict(title='OK', tags=['memory-card'], unused=True),
    'error': dict(title='Error', tags=['memory-card'], unused=True),
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    have = set()
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['gameId'] == GAME_ID:
            have.update(data.get('frames', []))
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for m in json.loads((out / 'manifest.json').read_text()):
        if m['frame_hex'] in have:
            print('already in the archive:', m['what'])
            continue
        stem = f'spf2x-{m["name"]}'
        shutil.copy(out / 'lcd' / f'{m["name"]}.png', inbox / f'{stem}.png')
        meta = dict(**SCREENS[m['what']], **BASE)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'screens to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
