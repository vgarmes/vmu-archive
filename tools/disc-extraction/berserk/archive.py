"""Shared by prep.py and check.py: the extraction output and the archive's Berserk entries."""
import json
from pathlib import Path

GAME = 'Berserk: Millennium Falcon-hen – Wasurebana no Shō'
GAME_ID = 'berserk-millennium-falcon-hen-wasurebana-no-sho'  # its id in content/games.json
REPO = Path(__file__).resolve().parents[3]


def load(out):
    out = Path(out)
    manifest = json.loads((out / 'manifest.json').read_text())
    screens = {int(m['name']): m for m in manifest if m['kind'] == 'screen'}
    return screens, json.loads((out / 'animations.json').read_text())


def archive_entries(screens):
    """(id, data, disc screen numbers) for every archive entry of the game."""
    by_hex = {m['frame_hex']: n for n, m in screens.items()}
    for path in sorted((REPO / 'content/icons').glob('*.json')):
        data = json.loads(path.read_text())
        if data['gameId'] == GAME_ID:
            yield path.stem, data, [by_hex.get(h) for h in data['frames']]
