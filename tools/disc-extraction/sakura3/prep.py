"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes the screens listed in PICKS, one still each, and the animations in
ANIMS, converted with the rule a Flycast capture confirmed (value below 8 =
lit). ANIMS holds the animations a recording has timed; the rest wait, and so
do the faces' blink frames (every odd entry of a face file is the same
expression with the eyes closed). Anything with value 8 is refused until a
capture covers it.

Also writes the battle banners in BANNERS as scroll strips: the game slides
each one through the screen 1 px per 60 Hz tick (measured on a Flycast
recording of Gigantesque ciseau), so they import with stepPx 1 and delayMs 17.
A heroine's second and third banners are also in Ogami's files (attacks
together), so they carry both characters' tags.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

GAME = 'Sakura Taisen 3: Paris wa Moete Iru ka'
REPO = Path(__file__).resolve().parents[3]
BASE = dict(game=GAME, publisher='Sega', year=2001, region='JP')
FACES = {
    'mgkg_coq': ('Coquelicot', 'coquelicot'),
    'mgkg_eri': ('Erica', 'erica'),
    'mgkg_gly': ('Glycine', 'glycine'),
    'mgkg_han': ('Hanabi', 'hanabi'),
    'mgkg_oga': ('Ogami', 'ogami'),
    'mgkg_rob': ('Lobelia', 'lobelia'),
}
# (entry name, frame in its strip, title, tags)
PICKS = [
    ('system-01', 0, 'Crest', ['logo']),
    ('system-02', 0, 'Message', []),
    *[(f'{stem}-{k:02d}', 0, title, ['character', 'portrait', tag])
      for stem, (title, tag) in FACES.items() for k in (0, 2, 4, 6)],  # eyes-open frames
]
# Animations with timing from a Flycast recording: (entry name, title, tags, delay per
# frame in ms, poster frame, id of the entry it replaces or None).
ANIMS = [
    # Logo intro: a line opens to a lit screen, the logo unfolds from it. Each frame
    # lasts 100 ms (6 ticks) in the recording, then the logo stays up about 4 s
    # before the map; the hold here is for the loop.
    ('system-04', 'Title screen', ['logo'], [100] * 10 + [4000], 10,
     'sakura-taisen-3-paris-wa-moete-iru-ka-title-screen'),
]
LIT_BELOW = 8 * 17  # vmu.py stores brightness v as grey level v * 17
SCROLL = dict(stepPx=1, delayMs=17)
# (entry name, title as drawn, tags). Titles keep the art's spelling (no accents).
BANNERS = [
    ('boss_crow_n-00', 'Les destinees', ['boss']),
    ('boss_lion_n-00', 'Royal rage', ['boss']),
    ('boss_rabbit_n-00', 'Gigantesque ciseau', ['boss']),
    ('boss_scorpion_n-00', 'Les fleurs du mal', ['boss']),
    ('boss_snake_n-00', 'Le chant de la terre', ['boss']),
    ('coquelicot_f1_n-00', 'Magique bonbon', ['coquelicot']),
    ('coquelicot_f1_n-01', 'Lever le rideau', ['coquelicot', 'ogami']),
    ('coquelicot_f1_n-02', 'Amour escarpolette', ['coquelicot', 'ogami']),
    ('erica_f1_n-00', 'Sacre de lumiere', ['erica']),
    ('erica_f1_n-01', 'Paradisiaque porte', ['erica', 'ogami']),
    ('erica_f1_n-02', 'Alleluia', ['erica', 'ogami']),
    ('glycine_f1_n-00', 'Grosse Vague', ['glycine']),
    ('glycine_f1_n-01', 'Bleu raz de maree', ['glycine', 'ogami']),
    ('glycine_f1_n-02', 'Pegase aile', ['glycine', 'ogami']),
    # Japanese titles carry their reading: ids are slugs, and slugs keep only Latin letters.
    ('hanabi_f1_n-00', '北大路花火 一の舞 金枝玉葉 (Kitaōji Hanabi Ichi no Mai Kinshi Gyokuyō)', ['hanabi']),
    ('hanabi_f1_n-01', '落花流水 (Rakka Ryūsui)', ['hanabi', 'ogami']),
    ('hanabi_f1_n-02', '君と彷徨う恋の道かな (Kimi to Samayou Koi no Michi kana)', ['hanabi', 'ogami']),
    ('lobelia_f1_n-00', 'Fiamma Unghia', ['lobelia']),
    ('lobelia_f1_n-01', 'Combustione', ['lobelia', 'ogami']),
    ('lobelia_f1_n-02', 'Pericolo gioco', ['lobelia', 'ogami']),
    ('ogami_f1a_n-00', "狼虎滅却 刀光剣影 (Rōko Mekkyaku Tōkō Ken'ei)", ['ogami']),
    ('ogami_f1b_n-00', '狼虎滅却 疾風迅雷 (Rōko Mekkyaku Shippū Jinrai)', ['ogami']),
    ('ogami_f1c_n-00', "狼虎滅却 金甌無欠 (Rōko Mekkyaku Kin'ō Muketsu)", ['ogami']),
]


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    manifest = {m['name']: m for m in json.loads((out / 'manifest.json').read_text())}
    have = set()
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['game'] == GAME:
            have.update(data.get('frames', []))  # scroll entries store a strip instead
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for name, frame, title, tags in PICKS:
        m = manifest[name]
        assert not m['unverified'], f'{name} uses value 8, which no capture covers yet'
        if m['frame_hex'][frame] in have:
            print('already in the archive:', name)
            continue
        strip = Image.open(out / 'lcd' / f'{name}.png').convert('L')
        im = strip.crop((0, 32 * frame, 48, 32 * frame + 32)).point(lambda p: 0 if p < LIT_BELOW else 255)
        stem = f'sakura3-{name}-{frame:02d}'
        im.convert('1').save(inbox / f'{stem}.png')
        (inbox / f'{stem}.json').write_text(json.dumps(dict(title=title, **BASE, tags=tags), ensure_ascii=False, indent=1))
        written += 1
    for name, title, tags, delays, poster, replaces in ANIMS:
        m = manifest[name]
        assert not m['unverified'], f'{name} uses value 8, which no capture covers yet'
        assert len(delays) == m['frames'], f'{name} has {m["frames"]} frames, {len(delays)} delays'
        im = Image.open(out / 'lcd' / f'{name}.png').convert('L').point(lambda p: 0 if p < LIT_BELOW else 255)
        stem = f'sakura3-anim-{name}'
        im.convert('1').save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=tags, frameDelaysMs=delays, posterFrame=poster)
        if replaces:
            meta['replaces'] = replaces
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    for name, title, tags in BANNERS:
        m = manifest[name]
        assert m['height'] == 32 and m['frames'] == 0, f'{name} is not a banner strip'
        im = Image.open(out / 'lcd' / f'{name}.png').convert('L').point(lambda p: 0 if p < LIT_BELOW else 255)
        stem = f'sakura3-banner-{name}'
        im.convert('1').save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=['banner', *tags], scroll=SCROLL)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
