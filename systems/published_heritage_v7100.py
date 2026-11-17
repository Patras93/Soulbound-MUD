"""Read-only loading of published historical content. No runtime editor."""
from __future__ import annotations
import copy
import json
import os
import tempfile
from pathlib import Path
CONFIG_PATH=Path(__file__).resolve().parent.parent/'config'/'heritage_v7100.json'
_SETTINGS=None
_BASE_REGISTRY=None
def _registry():
    from core.classes_skills import RACES,CLASSES
    return RACES,CLASSES
def _lookup(kind,name):
    races,classes=_registry()
    entries=races if kind=='rasa' else classes
    for i,row in enumerate(entries):
        if row[0].casefold()==name.casefold():return i,row
    raise ValueError('Nieznana '+kind+': tylko istniejace nazwy z kreatora.')
def _validate(payload):
    if type(payload) is not dict or set(payload) not in (set(),{'races'},{'classes'},{'races','classes'}):
        raise ValueError('Niepoprawne ustawienia rodowodu.')
    data={'races':payload.get('races',{}),'classes':payload.get('classes',{})}
    if any(type(data[x]) is not dict or len(data[x])>64 for x in data):
        raise ValueError('Zbyt wiele zmian rodowodu.')
    for name,stats in data['races'].items():
        _lookup('rasa',name)
        if _BASE_REGISTRY is not None and name not in {row[0] for row in _BASE_REGISTRY[0]}:
            raise ValueError('Statystyki nowych ras edytuje sie tylko przy tworzeniu nowej rasy.')
        if (not isinstance(stats,list) or len(stats)!=5 or any(type(v) is not int or not 1<=v<=30 for v in stats)
                or sum(stats)!=50):
            raise ValueError('Rasa: dokladnie 50 punktow, 5 statystyk 1..30.')
    for name,weapon in data['classes'].items():
        _lookup('klasa',name)
        if _BASE_REGISTRY is not None and name not in {row[0] for row in _BASE_REGISTRY[1]}:
            raise ValueError('Klasy dodane edytuj przez rodowod nowa klasa.')
        if (not isinstance(weapon,str) or not 1<=len(weapon)<=70
                or any(ord(x)<32 or ord(x)==127 for x in weapon)):
            raise ValueError('Bron Duszy: nazwa 1..70 znakow bez sterujacych.')
    return data
def current():
    global _SETTINGS
    if _SETTINGS is None:
        if CONFIG_PATH.exists():
            raw=json.loads(CONFIG_PATH.read_text('utf-8'))
            if type(raw) is not dict or raw.get('schema')!=1:
                raise ValueError('Niepoprawny plik heritage_v7100.json.')
            _SETTINGS=_validate(raw.get('settings'))
        else:_SETTINGS={'races':{},'classes':{}}
    return copy.deepcopy(_SETTINGS)
def _apply(data):
    global _BASE_REGISTRY
    races, classes = _registry()
    if _BASE_REGISTRY is None:
        _BASE_REGISTRY = (tuple(races), tuple(classes))
    originals_r, originals_c = _BASE_REGISTRY
    if len(classes) < len(originals_c) or len(races) < len(originals_r):
        raise ValueError('Katalog klas lub ras zmienil rozmiar; odmowa odtwarzania.')
    # Custom playable races from v76 must survive edits to original race stats.
    # Refuse to touch an unrecognized extension (do not silently delete it).
    from sys import modules
    custom = modules.get('systems.published_races_v7600')
    extra_names = [row[0] for row in races[len(originals_r):]]
    if extra_names and (custom is None or set(extra_names) != set(custom.current())):
        raise ValueError('Nieznane nowe rasy w katalogu; odmowa nadpisania.')
    new_classes=modules.get('systems.published_classes_v7700')
    extra_classes={row[0] for row in classes[len(originals_c):]}
    if extra_classes and (new_classes is None or extra_classes != set(new_classes.current())):
        raise ValueError('Nieznane dodatkowe klasy w katalogu; odmowa nadpisania.')
    races[:] = originals_r
    classes[:] = originals_c
    for name, stats in data['races'].items():
        idx, old = _lookup('rasa', name)
        races[idx] = (old[0], old[1], *stats)
    for name, weapon in data['classes'].items():
        idx, old = _lookup('klasa', name)
        classes[idx] = (old[0], old[1], weapon, old[3])
    if custom is not None and custom._ORIGINAL_RACES is not None:
        custom.rebase_after_heritage()
    if new_classes is not None and new_classes._ORIGINAL is not None:
        new_classes.rebase_after_heritage()
def restore():
    _apply(current())
