"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG (frames stacked, in play order) and sidecar per script, skipping
any the archive already has (same screens, whichever frame it starts on). Scripts
the code never starts are marked "unused".
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

GAME = 'Bangai-O'
GAME_ID = 'bangai-o'  # its id in content/games.json
REPO = Path(__file__).resolve().parents[3]
BASE = dict(game=GAME, publisher='Treasure', year=1999)
# Only the katakana title screen is Japan's alone; the rest is English text.
JAPANESE_TEXT = {1}
TITLES = {
    0: ('Treasure logo', ['logo']),
    1: ('Title screen', ['logo']),
    2: ('Mode: Riki', ['character']),
    3: ('Mode: Riki', ['character']),
    4: ('Mode: Mami', ['character']),
    5: ('Mode: Mami', ['character']),
    6: ('Continue?', ['character']),
}


def archive_frames():
    for path in sorted((REPO / 'content/icons').glob('*.json')):
        data = json.loads(path.read_text())
        if data['gameId'] == GAME_ID:
            yield path.stem, data['frames']


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    by_name = {int(m['name']): m['frame_hex'] for m in json.loads((out / 'manifest.json').read_text())}
    anims = json.loads((out / 'animations.json').read_text())['animations']
    have = {frozenset(f) for _, f in archive_frames()}
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for a in anims:
        if frozenset(by_name[n] for n in a['screens']) in have:
            continue
        title, tags = TITLES[a['script']]
        # Unused scripts sort after the played ones, so the importer gives the played
        # loop the plain id ("mode-riki") and the unused one the suffix.
        stem = f'bangaioh-{"" if a["played"] else "unused-"}{a["script"]}-' + '-'.join(f'{n:02d}' for n in a['screens'])
        sheet = Image.new('1', (48, 32 * len(a['screens'])), 1)
        for k, n in enumerate(a['screens']):
            sheet.paste(Image.open(out / 'lcd' / f'{n:02d}.png').convert('1'), (0, 32 * k))
        sheet.save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, **({'region': 'ntsc-j'} if a['script'] in JAPANESE_TEXT else {}), tags=tags)
        delays = a.get('delays_ms')
        if delays:
            meta.update({'frameDelayMs': delays[0]} if len(set(delays)) == 1 else {'frameDelaysMs': delays})
        if not a['played']:
            meta['unused'] = True
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
