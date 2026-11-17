"""Read-only loading of published historical content. No runtime editor."""
from __future__ import annotations
import copy
import json
import os
import re
import tempfile
from pathlib import Path
from core.classes_skills import RACES, RACE_CLASS_RECOMMENDATIONS
from core.character_resources import (AUTHORED_RACE_PASSIVE_PROFILES,
                                      race_passive_text_pl, passive_text_pl)
from systems.custom_passives_v9500 import parse_profile, validate_profile
CONFIG_PATH=Path(__file__).resolve().parent.parent/'config'/'custom_races_v7600.json'
_ORIGINAL_RACES=None
_ORIGINAL_PASSIVES=None
_ORIGINAL_RECOMMENDATIONS=None
_SETTINGS=None
_MAX_NEW_RACES=32
_NAME=re.compile(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9 -]{1,27}\Z")
def _ensure_base():
    global _ORIGINAL_RACES,_ORIGINAL_PASSIVES,_ORIGINAL_RECOMMENDATIONS
    if _ORIGINAL_RACES is None:
        _ORIGINAL_RACES=tuple(copy.deepcopy(RACES))
        _ORIGINAL_PASSIVES=copy.deepcopy(AUTHORED_RACE_PASSIVE_PROFILES)
        _ORIGINAL_RECOMMENDATIONS=copy.deepcopy(RACE_CLASS_RECOMMENDATIONS)
    return _ORIGINAL_RACES
def _validated(rows):
    if type(rows) is not dict or len(rows)>_MAX_NEW_RACES:
        raise ValueError('Maksymalnie 32 nowe rasy w slowniku.')
    bases={row[0].casefold():row[0] for row in _ensure_base()}
    used=set(bases)
    result={}
    for name,setting in rows.items():
        if not isinstance(name,str) or not _NAME.fullmatch(name) or name.strip()!=name:
            raise ValueError('Nazwa rasy: 2-28 liter/cyfr/spacji/minusow, bez znakow sterujacych.')
        if name.casefold() in used:
            raise ValueError('Powtarzajaca sie nazwa rasy lub kolizja z oryginalna.')
        used.add(name.casefold())
        if type(setting) is not dict or not {'parent','stats'} <= set(setting) or set(setting)-{'parent','stats','passive_override'}:
            raise ValueError('Rasa musi posiadac parent oraz stats.')
        parent=setting['parent']; stats=setting['stats']
        if not isinstance(parent,str) or parent.casefold() not in bases:
            raise ValueError('Pasyw musi pochodzic z istniejacej rasy bazowej.')
        if type(stats) is not list or len(stats)!=5 or any(type(x) is not int or not 1<=x<=30 for x in stats) or sum(stats)!=50:
            raise ValueError('Wymagane 5 statystyk 1..30 o sumie dokladnie 50.')
        result[name]={'parent':bases[parent.casefold()], 'stats':list(stats)}
        if 'passive_override' in setting:result[name]['passive_override']=validate_profile(setting['passive_override'])
    return result
def current():
    global _SETTINGS
    if _SETTINGS is None:
        if CONFIG_PATH.is_file():
            raw=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            if type(raw) is not dict or set(raw)!={'schema','races'} or raw['schema']!=1:
                raise ValueError('Niepoprawny plik custom_races_v7600.json.')
            _SETTINGS=_validated(raw['races'])
        else:
            _SETTINGS={}
    return copy.deepcopy(_SETTINGS)
def _apply(rows):
    rows=_validated(rows)
    base=_ensure_base()
    existing={row[0] for row in base}
    expected=existing|set(current() if _SETTINGS is not None else {})
    if not all(row[0] in expected for row in RACES):
        raise ValueError('Nieznane dodatkowe rasy w katalogu; odmowa nadpisania.')
    # Preserve the identity of RACES imported throughout the server.
    RACES[:]=list(copy.deepcopy(base)) + [
        (name,'Nowa rasa. Pasyw: '+(passive_text_pl(**row['passive_override']) if 'passive_override' in row else race_passive_text_pl(row['parent']))+'.', *row['stats'])
        for name,row in rows.items()
    ]
    AUTHORED_RACE_PASSIVE_PROFILES.clear()
    AUTHORED_RACE_PASSIVE_PROFILES.update(copy.deepcopy(_ORIGINAL_PASSIVES))
    RACE_CLASS_RECOMMENDATIONS.clear()
    RACE_CLASS_RECOMMENDATIONS.update(copy.deepcopy(_ORIGINAL_RECOMMENDATIONS))
    for name,row in rows.items():
        AUTHORED_RACE_PASSIVE_PROFILES[name]=copy.deepcopy(row.get('passive_override',_ORIGINAL_PASSIVES[row['parent']]))
        RACE_CLASS_RECOMMENDATIONS[name]=copy.deepcopy(_ORIGINAL_RECOMMENDATIONS[row['parent']])
def restore():
    _apply(current())
def rebase_after_heritage():
    """Rebuild additive races after a validated edit to original race budgets."""
    global _ORIGINAL_RACES
    _ORIGINAL_RACES=tuple(copy.deepcopy(RACES))
    _apply(current())
