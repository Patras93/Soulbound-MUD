# -*- coding: utf-8 -*-
"""Admin Live v52: persistent, server-wide caps for eight progression axes.

This is deliberately not an OLC quest DRAFT: live caps take effect immediately
on the running server, require owner confirmation, and are persisted atomically
without modifying the player SQLite database.

'bez limitu' is represented on disk as null. Legacy modules use a generous
numeric compatibility ceiling; the service itself retains the true 'no user cap'
semantic. Engine integer/SQLite limits still exist and are reported to owners.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAP_FILE = ROOT / 'LIVE_CONTENT' / 'admin_level_caps.json'
# The legacy engine performs integer arithmetic and persists to SQLite int64.
# This is a technical safety ceiling, not a gameplay level cap.
TECHNICAL_CEILING = 1_000_000_000
DEFAULT = 800
# Smithing EQ improvement (+10) is independent of the item's required level (800).
DEFAULTS = {'postac':800, 'bieglosc':800, 'dusza':800, 'bron_duszy':800,
            'skille':800, 'profesje':800, 'narzedzia':800, 'gildia':800,
            'eq':800, 'ulepszenia_eq':10}
KEYS = tuple(DEFAULTS)
OLD_KEYS_V52 = KEYS[:8]
LABELS = {
    'postac':'Postac', 'bieglosc':'Bieglosc klas', 'dusza':'Soul Level',
    'bron_duszy':'Bieglosc Broni Duszy', 'skille':'Skille',
    'profesje':'Profesje', 'narzedzia':'Narzedzia', 'gildia':'Gildia',
    'eq':'Poziom EQ', 'ulepszenia_eq':'Ulepszanie EQ (+)',
}
ALIASES = {
    'postac':'postac','character':'postac','level':'postac',
    'bieglosc':'bieglosc','klasy':'bieglosc','klasa':'bieglosc',
    'dusza':'dusza','soul':'dusza',
    'bron':'bron_duszy','bron_duszy':'bron_duszy','bronduszy':'bron_duszy',
    'skille':'skille','skill':'skille','umiejetnosci':'skille',
    'profesje':'profesje','profesja':'profesje',
    'narzedzia':'narzedzia','narzedzie':'narzedzia',
    'gildia':'gildia','guild':'gildia',
    'eq':'eq', 'sprzet':'eq', 'ekwipunek':'eq', 'poziom_eq':'eq',
    'ulepszenia_eq':'ulepszenia_eq', 'ulepszanie_eq':'ulepszenia_eq',
    'ulepsz_eq':'ulepszenia_eq', 'eq_plus':'ulepszenia_eq',
}
# Only actual level-cap globals. Tier unlocks, combat tier curves, item unlocks,
# quest requirements and guild buildings remain separate authored systems.
GLOBAL_NAMES = {
    'CHARACTER_MAX_LEVEL':'postac', 'CLASS_MASTERY_MAX_LEVEL':'bieglosc',
    'SOUL_MAX_LEVEL':'dusza', 'SOUL_WEAPON_MASTERY_MAX_LEVEL':'bron_duszy',
    'SKILL_MAX_LEVEL':'skille', 'PROFESSION_MAX_LEVEL':'profesje',
    'BLACKSMITHING_MAX_LEVEL':'profesje','JEWELCRAFTING_MAX_LEVEL':'profesje',
    'TOOL_MAX_LEVEL':'narzedzia', 'V0926_GUILD_MAX_LEVEL':'gildia',
    'EQUIPMENT_MAX_LEVEL':'eq', 'V03042_EQ_UPGRADE_MAX':'ulepszenia_eq',
}
# Do not rewrite audit classes, resource generation limits or shared configuration
# on a running world. A module's imported cap bindings are refreshed in place.
MODULE_PREFIXES = ('core.', 'config.', 'player.', 'storage.', 'world.', 'network.', 'systems.')
_state = dict(DEFAULTS)
_loaded = False


def normalize_key(value):
    text = str(value or '').strip().lower().replace('-', '_')
    key = ALIASES.get(text)
    if key is None:
        raise ValueError('Nieznana dziedzina. Wpisz admin live limity.')
    return key


def parse_limit(value):
    raw = str(value).strip().lower().replace(' ', '')
    if raw in ('bezlimitu', 'bez_limit', 'nielimitowany', 'unlimited', 'inf', 'nieskonczony'):
        return None
    if not raw.isdecimal() or len(raw) > 10:
        raise ValueError('Limit: podaj liczbe 1-10000000 albo bezlimitu.')
    level = int(raw)
    if not 1 <= level <= 10_000_000:
        raise ValueError('Limit: dopuszczalne 1-10000000 lub bezlimitu.')
    return level


def read_file(path=None):
    path = CAP_FILE if path is None else path
    if not Path(path).exists():
        return dict(DEFAULTS)
    with Path(path).open('r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict) or data.get('schema') != 1 or not isinstance(data.get('caps'), dict):
        raise ValueError('Plik limitow ma niezgodny format. Nie zmieniono ustawien.')
    # Read older v52 settings without dropping custom limits or rewriting disk.
    # New EQ axes receive their historical defaults until explicitly changed.
    supplied=set(data['caps'])
    if supplied not in (set(KEYS), set(OLD_KEYS_V52)):
        raise ValueError('Plik limitow: brakuje dziedzin lub wystepuja obce pola.')
    result = {}
    for key in KEYS:
        value = data['caps'].get(key, DEFAULTS[key])
        if value is None:
            result[key] = None
        elif type(value) is int and 1 <= value <= 10_000_000:
            result[key] = value
        else:
            raise ValueError('Plik limitow: bledna wartosc '+key)
    return result


def _atomic_write(values, path=None):
    path = CAP_FILE if path is None else path
    target=Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload=json.dumps({'schema':1, 'caps':values},ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    handle, tmp=tempfile.mkstemp(prefix='.level_caps_',suffix='.tmp',dir=str(target.parent))
    try:
        with os.fdopen(handle,'w',encoding='utf-8',newline='\n') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def effective_number(value):
    return TECHNICAL_CEILING if value is None else int(value)


def display(value):
    return 'bez limitu' if value is None else str(int(value))


def _apply_to_runtime():
    numbers={name:effective_number(_state[key]) for name,key in GLOBAL_NAMES.items()}
    for mod_name,module in list(sys.modules.items()):
        if module is None:continue
        # server.py also hosts compatibility-bound legacy methods: their
        # FunctionType.__globals__ points to server.py's own live namespace.
        # Never touch an unrelated application's __main__ namespace.
        server_host=(mod_name in ('server','__main__') and
                     str(getattr(module,'__file__','')).replace('\\','/').endswith('/server.py'))
        if not mod_name.startswith(MODULE_PREFIXES) and not server_host:
            continue
        mapping=vars(module)
        # modules may bind a function or unrelated variable with similar name;
        # update only integer cap bindings, and never tier/quest/catalog thresholds.
        for name,num in numbers.items():
            if type(mapping.get(name)) is int:
                setattr(module,name,num)
    # Recompute requirements only for generated infinite-depth EQ. Never touch
    # authored catalog items, stored player inventory or the SQLite database.
    infinite=sys.modules.get('systems.infinite_equipment')
    if infinite is not None:
        refresh=getattr(infinite,'refresh_infinite_equipment_requirements_v5300',None)
        if callable(refresh):refresh()


def load(*,path=None,apply=True):
    global _loaded
    values=read_file(path)
    _state.update(values)
    _loaded=True
    if apply:_apply_to_runtime()
    return dict(_state)


def current():
    # Reading a default must not apply saved overrides during the early
    # native-runtime bootstrap, whose static authoring audits require 800.
    # server.py loads persistent overrides explicitly after native assembly.
    return dict(_state)


def cap(kind):
    return current()[normalize_key(kind)]


def can_grow(kind, level):
    maximum=cap(kind)
    return maximum is None or int(level) < maximum


def _guard_persisted_state(path):
    source=Path(CAP_FILE if path is None else path)
    if source.exists() and read_file(source) != current():
        raise ValueError('Plik limitow zmienil sie poza admin live. Uzyj: admin live limity wczytaj POTWIERDZAM.')


def change(kind, value, *, path=None):
    # Commit disk first; only apply in-memory changes when persistence succeeds.
    key=normalize_key(kind)
    parsed=parse_limit(value)
    _guard_persisted_state(path)
    previous=current()
    if previous[key] == parsed:
        return key,previous[key],parsed,False
    next_values=dict(previous)
    next_values[key]=parsed
    _atomic_write(next_values,path)
    _state.update(next_values)
    _apply_to_runtime()
    return key,previous[key],parsed,True


def reset(kind,*,path=None):
    key=normalize_key(kind)
    return change(key,str(DEFAULTS[key]),path=path)


def describe(page=None):
    values=current()
    if page is None:
        return 'LIMITY POZIOMOW: '+ '; '.join(f'{LABELS[k]} {display(values[k])}' for k in KEYS)+'. Statystyki bazowe: bez limitu. EQ to poziom wymagań przedmiotu, ulepszenia EQ to oddzielny limit +10. Progi założenia EQ nadal obowiązują. Soul Tier i budynki gildii są osobne.'
    key=normalize_key(page)
    return f'LIMITY {LABELS[key]}: teraz {display(values[key])}, domyslnie {DEFAULTS[key]}. Zmiana: admin live limity ustaw {key} 1200 POTWIERDZAM lub bezlimitu. Reset: admin live limity reset {key} POTWIERDZAM.'


def change_all(value,*,path=None):
    parsed=parse_limit(value)
    _guard_persisted_state(path)
    previous=current()
    next_values={key:parsed for key in KEYS}
    if previous==next_values:return previous,next_values,False
    _atomic_write(next_values,path)
    _state.update(next_values)
    _apply_to_runtime()
    return previous,next_values,True


def reset_all(*,path=None):
    _guard_persisted_state(path)
    previous=current()
    new_values=dict(DEFAULTS)
    if previous==new_values:return previous,new_values,False
    _atomic_write(new_values,path)
    _state.update(new_values)
    _apply_to_runtime()
    return previous,new_values,True
