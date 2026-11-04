"""Turn vmu.py's and app.py's output into input for `pnpm icons:import`.

    python3 prep.py <vmu.py out dir> <app.py out dir> <inbox dir>

Writes one PNG (frames stacked, in play order) and sidecar per screen or
animation, and one per sprite, skipping screens the archive already has.
Only what's Japanese gets region JP: the katakana logo and the graffiti
viewer's screens with Japanese text. The rest (the radio, Now Saving/Loading,
OK, NG, the SEGA screens, every font) is byte for byte the same on the US disc.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

GAME = 'Jet Set Radio'
REPO = Path(__file__).resolve().parents[3]
BASE = dict(game=GAME, publisher='Sega', year=2000)
GAME_SCREENS = {
    'logo': ('Logo', ['logo'], 'JP'),
    'radio': ('Radio', [], None),
    'now-saving': ('Now Saving', ['memory-card'], None),
    'now-loading': ('Now Loading', ['memory-card'], None),
    'ok': ('OK', ['memory-card'], None),
    'ng': ('NG', ['memory-card'], None),
}
VIEWER = 'Graffiti viewer'
APP_FILE = '/JETRADIO/SYSOPTION.AFS'
APP_SCREENS = {
    'sega': ('SEGA', ['logo'], None),
    'copyright': ('copyright', [], None),
    'title': ('title', ['logo'], 'JP'),
    'channel': ('downloaded graffiti', ['menu'], 'JP'),
    'size-menu': ('size menu', ['menu'], 'JP'),
    'no-graffiti': ('no graffiti', ['menu'], 'JP'),
}
APP_SPRITES = {
    'radio-1': ('radio, left', []),
    'radio-2': ('radio, middle', []),
    'radio-3': ('radio, right', []),
    'font-title': ('title font', ['font', 'sheet']),
    'font-narrow': ('narrow font', ['font', 'sheet']),
    'font-wide': ('wide font', ['font', 'sheet']),
    'font-kana': ('kana font', ['font', 'sheet']),
    'font-small': ('small font', ['font', 'sheet']),
    'font-hex': ('hex digits', ['font', 'digits', 'sheet']),
}


def slug(s):
    return '-'.join(''.join(c if c.isalnum() else ' ' for c in s.lower()).split())


def screen_id(name):
    # What `pnpm icons:import` names it (newId in scripts/import.ts).
    return f'{slug(GAME)}-{slug(f"{VIEWER}: {APP_SCREENS[name][0]}")}'


def write(inbox, stem, im, meta):
    im.save(inbox / f'{stem}.png')
    (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))


def with_region(meta, region):
    return dict(meta, region=region) if region else meta


def main(game_out, app_out, inbox):
    # File names start jsr-1- (screens) and jsr-2- (sprites): the importer goes
    # in name order, and a sprite's drawnAt needs its screen imported first.
    game_out, app_out, inbox = Path(game_out), Path(app_out), Path(inbox)
    have = set()
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['game'] == GAME:
            have.add(tuple(data['frames']))
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0

    by_name = {int(m['name']): m['frame_hex'] for m in json.loads((game_out / 'manifest.json').read_text())}
    for a in json.loads((game_out / 'animations.json').read_text())['animations']:
        if tuple(by_name[n] for n in a['screens']) in have:
            print('already in the archive:', a['name'])
            continue
        title, tags, region = GAME_SCREENS[a['name']]
        sheet = Image.new('1', (48, 32 * len(a['screens'])), 1)
        for k, n in enumerate(a['screens']):
            sheet.paste(Image.open(game_out / 'lcd' / f'{n:02d}.png').convert('1'), (0, 32 * k))
        meta = with_region(dict(title=title, **BASE, tags=tags), region)
        if a.get('delay_ms'):
            meta['frameDelayMs'] = a['delay_ms']
        write(inbox, f'jsr-1-{a["name"]}', sheet, meta)
        written += 1

    app = json.loads((app_out / 'manifest.json').read_text())
    for s in app['screens']:
        name = s['name']
        if tuple(s['frames']) in have:
            print('already in the archive:', name)
            continue
        title, tags, region = APP_SCREENS[name]
        im = Image.open(app_out / 'screens' / f'{name}.png').convert('1')
        meta = with_region(dict(title=f'{VIEWER}: {title}', **BASE, tags=['graffiti-viewer'] + tags), region)
        write(inbox, f'jsr-1-app-{name}', im, meta)
        written += 1
    for s in app['sprites']:
        title, tags = APP_SPRITES[s['name']]
        meta = dict(title=f'{VIEWER}: {title}', **BASE, tags=['graffiti-viewer'] + tags, sprite=True,
                    source=dict(file=APP_FILE, entry=app['member'], offset=app['member_offset'] + s['offset']))
        if s['drawn_at']:
            meta['drawnAt'] = [dict(screen=screen_id(n), x=x, y=y) for n, x, y in s['drawn_at']]
        write(inbox, f'jsr-2-app-sprite-{s["name"]}', Image.open(app_out / 'sprites' / f'{s["name"]}.png'), meta)
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
