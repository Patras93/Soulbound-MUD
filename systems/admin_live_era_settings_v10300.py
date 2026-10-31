# -*- coding: utf-8 -*-
"""Small, bounded, persistent Admin Live Era DRAFT for high-dungeon XP.

Does not edit quest definitions or player SQLite. A single in-process DRAFT,
optimistic base revision and an atomic published config are kept separate.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

CONFIG_PATH = Path(__file__).resolve().parent.parent / 'LIVE_CONTENT' / 'era_v10300.json'
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


def _atomic_save(config):
    _validate(config)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with NamedTemporaryFile('w', encoding='utf-8', dir=CONFIG_PATH.parent,
                                prefix='.era_', suffix='.tmp', delete=False) as out:
            temp_name = out.name
            json.dump(config, out, ensure_ascii=False, indent=2, sort_keys=True)
            out.write('\n')
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp_name, CONFIG_PATH)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def reset_for_tests():
    global _cache, _draft, _draft_baseline
    _cache = _draft = _draft_baseline = None


def _formatted(settings):
    return '; '.join(f'{LABELS[k]} {settings[k]}%' for k in KINDS)


def command(tail):
    global _cache, _draft, _draft_baseline
    parts = str(tail or '').casefold().split()
    action = parts[0] if parts else ''
    if action in ('', 'pomoc', 'help'):
        return ('ERA PREMIE: podglad / ustaw RODZAJ PROCENT / sprawdz / porownaj / '
                'aktywuj POTWIERDZAM / anuluj / cofnij POTWIERDZAM. '
                'Rodzaje: deep, krypta, krypta_mityczna, wieza, wieza_mityczna. '
                'Zakres 100–200%; działa tylko od piętra 801. DRAFT nie zmienia świata.')
    try:
        current = _load()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return f'ERA: nie można wczytać zapisu ({type(exc).__name__}). Nie zmieniono danych.'
    if action in ('podglad', 'status') and len(parts) == 1:
        return f'ERA rewizja {current["rev"]}: {_formatted(current["bonus"])}. ' + (
            f'DRAFT: {_formatted(_draft)}.' if _draft is not None else 'Brak zmian DRAFT.')
    if action == 'ustaw' and len(parts) == 3:
        kind = ALIASES.get(parts[1])
        if not kind:
            return 'ERA: nieznany rodzaj lochu. Wpisz admin live era premie pomoc.'
        if not parts[2].isascii() or not parts[2].isdecimal() or len(parts[2]) > 3:
            return 'ERA: podaj całkowity procent 100–200.'
        pct = int(parts[2])
        if not 100 <= pct <= 200:
            return 'ERA: podaj całkowity procent 100–200.'
        if _draft is None:
            _draft = dict(current['bonus'])
            _draft_baseline = current['rev']
        _draft[kind] = pct
        return f'ERA DRAFT: {LABELS[kind]} = {pct}%. Aktywne premie bez zmian. Użyj sprawdz i porownaj.'
    if action == 'sprawdz' and len(parts) == 1:
        if _draft is None:
            return 'ERA: brak zmian DRAFT.'
        try:
            disk = _read_file()
        except (OSError, ValueError):
            return 'ERA: plik zapisu jest niepoprawny. Nic nie zmieniono.'
        if _draft_baseline != disk['rev']:
            return 'ERA: rewizja na dysku zmieniła się. Anuluj DRAFT i wczytaj ponownie.'
        if set(_draft) != set(KINDS) or any(not 100 <= v <= 200 for v in _draft.values()):
            return 'ERA: niepoprawny DRAFT.'
        return 'ERA: DRAFT poprawny. Wartości 100–200%, tylko piętra 801+, bez zmian EXP graczy i SQLite.'
    if action == 'porownaj' and len(parts) == 1:
        if _draft is None:
            return 'ERA: brak zmian DRAFT.'
        changed = [f'{LABELS[k]}: {current["bonus"][k]}% → {_draft[k]}%'
                   for k in KINDS if _draft[k] != current['bonus'][k]]
        return 'ERA: ' + ('; '.join(changed) if changed else 'brak różnic') + '.'
    if action == 'anuluj' and len(parts) == 1:
        _draft = _draft_baseline = None
        return 'ERA: anulowano tylko DRAFT premii Ery. Aktywne wartości bez zmian.'
    if action == 'aktywuj' and len(parts) == 2 and parts[1] == 'potwierdzam':
        if _draft is None:
            return 'ERA: brak zmian DRAFT.'
        try:
            disk = _read_file()
        except (OSError, ValueError):
            return 'ERA: plik zapisu jest niepoprawny. Nic nie zmieniono.'
        if disk['rev'] != _draft_baseline:
            return 'ERA: konflikt rewizji. Zmiany nie zostały opublikowane.'
        if _draft == disk['bonus']:
            _draft = _draft_baseline = None
            return 'ERA: DRAFT jest identyczny z aktywnym ustawieniem.'
        new = {'schema': 1, 'rev': disk['rev'] + 1,
               'bonus': dict(_draft), 'previous': dict(disk['bonus'])}
        _atomic_save(new)
        _cache = new
        _draft = _draft_baseline = None
        return f'ERA: opublikowano rewizję {new["rev"]}, bez restartu. {_formatted(new["bonus"])}.'
    if action == 'cofnij' and len(parts) == 2 and parts[1] == 'potwierdzam':
        if _draft is not None:
            return 'ERA: anuluj najpierw DRAFT, aby bezpiecznie cofnąć publikację.'
        try:
            disk = _read_file()
        except (OSError, ValueError):
            return 'ERA: plik zapisu jest niepoprawny. Nic nie zmieniono.'
        if disk['previous'] is None:
            return 'ERA: nie ma poprzedniej opublikowanej konfiguracji.'
        new = {'schema': 1, 'rev': disk['rev'] + 1,
               'bonus': dict(disk['previous']), 'previous': dict(disk['bonus'])}
        _atomic_save(new)
        _cache = new
        return f'ERA: cofnięto ostatnią publikację, nowa rewizja {new["rev"]}. {_formatted(new["bonus"])}.'
    return 'ERA: nieznane polecenie. Wpisz admin live era premie pomoc.'
