"""Read-only loading of published historical content. No runtime editor."""
from __future__ import annotations
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config' / 'era_v10300.json'
KINDS = ('deep', 'crypt', 'mythic_crypt', 'tower', 'mythic_tower')
LABELS = {'deep': 'Deep Dungeon', 'crypt': 'Krypta',
          'mythic_crypt': 'Mityczna Krypta', 'tower': 'Wieża Astralna',
          'mythic_tower': 'Mityczna Wieża'}
ALIASES = {'deep': 'deep', 'krypta': 'crypt', 'crypt': 'crypt',
           'krypta_mityczna': 'mythic_crypt', 'mythic_crypt': 'mythic_crypt',
           'wieza': 'tower', 'tower': 'tower',
           'wieza_mityczna': 'mythic_tower', 'mythic_tower': 'mythic_tower'}
_cache = None
_draft = None
_draft_baseline = None
def _defaults():
    return {kind: 100 for kind in KINDS}
def _validate(obj):
    if not isinstance(obj, dict) or set(obj) != {'schema', 'rev', 'bonus', 'previous'} or obj['schema'] != 1:
        raise ValueError('Niepoprawny format zapisanych premii Ery.')
    if type(obj['rev']) is not int or not 0 <= obj['rev'] <= 10**9:
        raise ValueError('Niepoprawna rewizja premii Ery.')
    for value in (obj['bonus'], obj['previous']):
        if value is None:
            continue
        if type(value) is not dict or set(value) != set(KINDS):
            raise ValueError('Niekompletny zapis premii Ery.')
        if any(type(v) is not int or not 100 <= v <= 200 for v in value.values()):
            raise ValueError('Premia Ery musi byc w zakresie 100–200%.')
    if obj['bonus'] is None:
        raise ValueError('Brak aktywnych premii Ery.')
    return obj
def _read_file():
    if not CONFIG_PATH.exists():
        return {'schema': 1, 'rev': 0, 'bonus': _defaults(), 'previous': None}
    return _validate(json.loads(CONFIG_PATH.read_text(encoding='utf-8')))
def _load():
    global _cache
    if _cache is None:
        _cache = _read_file()
    return _cache
def active_bonus_pct(kind):
    return int(_load()['bonus'].get(kind, 100))
