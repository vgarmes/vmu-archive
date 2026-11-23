"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG (frames stacked, in play order) and sidecar per animation.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

# Released in Japan alone.
BASE = dict(game='Rainbow Cotton', publisher='Success', year=2000, region='ntsc-j')
TITLES = {
    0: ('Title logo', ['logo', 'title']),
    1: ('Now loading', ['status']),
    2: ('Blinking', ['character']),
    3: ('Seeing stars', ['character', 'reaction']),
    4: ('Dizzy', ['character', 'reaction']),
    **{k: ('Talking', ['character']) for k in range(5, 11)},
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    anims = json.loads((out / 'animations.json').read_text())['animations']
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    for a in anims:
        title, tags = TITLES[a['number']]
        stem = f'rainbow-cotton-{a["number"]:02d}-' + title.lower().replace(' ', '-')
        sheet = Image.new('1', (48, 32 * len(a['screens'])), 1)
        for k, n in enumerate(a['screens']):
            sheet.paste(Image.open(out / 'screens' / f'{n:02d}.png').convert('1'), (0, 32 * k))
        sheet.save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=tags)
        delays = a['delays_ms']
        if len(delays) > 1:
            meta.update({'frameDelayMs': delays[0]} if len(set(delays)) == 1 else {'frameDelaysMs': delays})
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(len(anims), 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
