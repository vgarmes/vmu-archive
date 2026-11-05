"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG (frames stacked, in play order) and sidecar per animation,
skipping any the archive already has.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

GAME = 'Crazy Taxi 2'
GAME_ID = 'crazy-taxi-2'  # its id in content/games.json
REPO = Path(__file__).resolve().parents[3]
# The name and logo are the same in every release, so nothing gets a region.
BASE = dict(game=GAME, publisher='Sega', year=2001)
TITLES = {
    'logo': ('Title screen', ['logo']),
    'loading': ('Now Loading', ['memory-card']),
    'saving': ('Now Saving', ['memory-card']),
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    by_name = {int(m['name']): m['frame_hex'] for m in json.loads((out / 'manifest.json').read_text())}
    anims = json.loads((out / 'animations.json').read_text())['animations']
    have = set()
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['gameId'] == GAME_ID:
            have.add(frozenset(data['frames']))
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for a in anims:
        if frozenset(by_name[n] for n in a['screens']) in have:
            print('already in the archive:', a['name'])
            continue
        title, tags = TITLES[a['name']]
        stem = f'crazytaxi2-{a["name"]}'
        sheet = Image.new('1', (48, 32 * len(a['screens'])), 1)
        for k, n in enumerate(a['screens']):
            sheet.paste(Image.open(out / 'lcd' / f'{n:02d}.png').convert('1'), (0, 32 * k))
        sheet.save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=tags)
        if a.get('delays_ms'):
            meta['frameDelayMs'] = a['delays_ms'][0]
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
