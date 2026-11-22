"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per screen or sprite.
"""
import json
import shutil
import sys
from pathlib import Path

# Released in Japan alone.
BASE = dict(game='Tokyo Bus Guide', publisher='Fortyfive', year=1999, region='ntsc-j')
QUIZ = 'Traffic sign quiz'
SCREENS = {
    'bus': dict(title='Bus', tags=['vehicle']),
    'danger': dict(title='Danger', tags=['status']),
    'now-loading': dict(title='Now loading', tags=['system']),
    'quiz-title': dict(title=f'{QUIZ}: title', tags=['minigame', 'logo']),
    'quiz-no-battery': dict(title=f'{QUIZ}: no battery', tags=['minigame', 'system']),
    'quiz-version': dict(title=f'{QUIZ}: version', tags=['minigame'], unused=True),
}
SPRITES = {
    'quiz-circle': dict(title=f'{QUIZ}: circle', tags=['minigame']),
    'quiz-cross': dict(title=f'{QUIZ}: cross', tags=['minigame']),
    'quiz-arrow-right': dict(title=f'{QUIZ}: right arrow', tags=['minigame']),
    'quiz-arrow-left': dict(title=f'{QUIZ}: left arrow', tags=['minigame']),
    'quiz-font': dict(title=f'{QUIZ}: font', tags=['minigame', 'font'],
                      glyphs=dict(height=8, width=8)),
}


def meta_for(m):
    name = m['name']
    if name.startswith('quiz-sign-'):
        meta = dict(title=f'{QUIZ}: sign {name[-2:]}', tags=['minigame'])
    elif m['kind'] == 'sprites':
        meta = dict(SPRITES[name])
    else:
        meta = dict(SCREENS[name])
    if m['kind'] == 'sprites':
        meta['sprite'] = True
        meta['source'] = {k: v for k, v in (('file', m['source']), ('entry', m.get('entry')),
                                            ('offset', m['offset'])) if v is not None}
    elif 'delay' in m:
        meta['frameDelayMs'] = m['delay']
    return dict(**meta, **BASE)


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    manifest = json.loads((out / 'manifest.json').read_text())
    for m in manifest:
        stem = f'tbg-{m["name"]}'
        shutil.copy(out / m['kind'] / f'{m["name"]}.png', inbox / f'{stem}.png')
        (inbox / f'{stem}.json').write_text(json.dumps(meta_for(m), ensure_ascii=False, indent=1))
    print(len(manifest), 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
