"""Read-only loading of published historical content. No runtime editor."""
from __future__ import annotations
import copy
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path
from core.classes_skills import (CLASSES,CLASS_SKILLS,CLASS_DESCRIPTIONS,
                                 CLASS_STARTING_STAT_BONUSES)
from core.character_resources import (AUTHORED_CLASS_PASSIVE_PROFILES,
                                      class_passive_text_pl, passive_text_pl)
from systems.custom_passives_v9500 import parse_profile, validate_profile
CONFIG_PATH=Path(__file__).resolve().parent.parent/'config'/'custom_classes_v7700.json'
_ORIGINAL=None
_SETTINGS=None
MAX_CLASSES=32
NAME_RE=re.compile(r'[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9 -]{1,27}\Z')
PARENTS=tuple(row[0] for row in CLASSES)  # All authored, gameplay-tested base archetypes
def _slug(value):
    normalized=unicodedata.normalize('NFKD',value.replace('ł','l').replace('Ł','L'))
    ascii_name=''.join(x for x in normalized if not unicodedata.combining(x)).lower()
    return re.sub(r'[^a-z0-9]+','_',ascii_name).strip('_')
def _base():
    global _ORIGINAL
    if _ORIGINAL is None:
        _ORIGINAL={
            'classes':tuple(copy.deepcopy(CLASSES)),
            'skills':{k:copy.deepcopy(v) for k,v in CLASS_SKILLS.items()},
            'descriptions':copy.deepcopy(CLASS_DESCRIPTIONS),
            'stat_bonuses':copy.deepcopy(CLASS_STARTING_STAT_BONUSES),
            'passives':copy.deepcopy(AUTHORED_CLASS_PASSIVE_PROFILES),
        }
    return _ORIGINAL
def _validated(rows):
    base=_base()
    if type(rows) is not dict or len(rows)>MAX_CLASSES:
        raise ValueError('Dopuszczalne maksymalnie 32 nowe klasy.')
    existing={row[0].casefold() for row in base['classes']}
    used_slugs=set()
    output={}
    for name,row in rows.items():
        if not isinstance(name,str) or NAME_RE.fullmatch(name) is None or name!=name.strip():
            raise ValueError('Nazwa klasy: 2-28 znakow, tylko litery, cyfry, spacja i minus.')
        if name.casefold() in existing:raise ValueError('Powtorzona nazwa klasy.')
        existing.add(name.casefold())
        slug=_slug(name)
        if slug in used_slugs:raise ValueError('Kolizja identyfikatorow klas po uproszczeniu znakow.')
        used_slugs.add(slug)
        if type(row) is not dict or not {'parent','weapon'} <= set(row) or (set(row)-{'parent','weapon','skill_parent','passive_parent','passive_override'}):
            raise ValueError('Klasa wymaga parent i weapon; opcjonalnie skill_parent oraz passive_parent.')
        parent=row['parent'];weapon=row['weapon']
        skill_parent=row.get('skill_parent',parent)
        passive_parent=row.get('passive_parent',parent)
        for label,source in (('Baza',parent),('Skille',skill_parent),('Pasyw',passive_parent)):
            if type(source) is not str or source not in PARENTS:
                raise ValueError(f'{label}: wybierz jedna z {len(PARENTS)} istniejacych klas bazowych.')
        if not base['skills'].get(skill_parent) or passive_parent not in base['passives'] or parent not in base['stat_bonuses']:
            raise ValueError('Wskazany archetyp nie ma kompletnej mechaniki do dziedziczenia.')
        if type(weapon) is not str or not 1<=len(weapon)<=70 or weapon.strip()!=weapon or any(ord(c)<32 or ord(c)==127 for c in weapon):
            raise ValueError('Bron Duszy: 1-70 znakow bez sterujacych.')
        # Backward compatible with schema 1 and pre-v91 classes; no migration.
        output[name]={'parent':parent,'weapon':weapon}
        if 'skill_parent' in row:output[name]['skill_parent']=skill_parent
        if 'passive_parent' in row:output[name]['passive_parent']=passive_parent
        if 'passive_override' in row:output[name]['passive_override']=validate_profile(row['passive_override'])
    return output
def current():
    global _SETTINGS
    if _SETTINGS is None:
        if CONFIG_PATH.is_file():
            raw=json.loads(CONFIG_PATH.read_text('utf-8'))
            if type(raw) is not dict or set(raw)!={'schema','classes'} or raw['schema']!=1:
                raise ValueError('Niepoprawny plik custom_classes_v7700.json.')
            _SETTINGS=_validated(raw['classes'])
        else:_SETTINGS={}
    return copy.deepcopy(_SETTINGS)
def _apply(rows):
    rows=_validated(rows)
    base=_base()
    original_count=len(base['classes'])
    observed={row[0] for row in CLASSES[original_count:]}
    if observed-set(current() if _SETTINGS is not None else {}):
        raise ValueError('Nieznana klasa w katalogu: nie nadpisuje zmian z innego modulu.')
    CLASSES[:]=list(copy.deepcopy(base['classes']))
    for index,name in enumerate(list(CLASS_SKILLS)):
        if name not in base['skills']:
            del CLASS_SKILLS[name]
    CLASS_DESCRIPTIONS.clear();CLASS_DESCRIPTIONS.update(copy.deepcopy(base['descriptions']))
    CLASS_STARTING_STAT_BONUSES.clear();CLASS_STARTING_STAT_BONUSES.update(copy.deepcopy(base['stat_bonuses']))
    AUTHORED_CLASS_PASSIVE_PROFILES.clear();AUTHORED_CLASS_PASSIVE_PROFILES.update(copy.deepcopy(base['passives']))
    for name,definition in rows.items():
        parent=definition['parent'];weapon=definition['weapon'];slug=_slug(name)
        skill_parent=definition.get('skill_parent',parent)
        passive_parent=definition.get('passive_parent',parent)
        source=next(r for r in base['classes'] if r[0]==parent)
        CLASSES.append((name,source[1],weapon,source[3]))
        CLASS_DESCRIPTIONS[name]=(f'Klasa {name}: bazowa mechanika {parent}, '+
                                  f'umiejetnosci {skill_parent}, pasyw {passive_parent}, '+
                                  f'wlasna Bron Duszy {weapon}. '+
                                  f'Pasyw: {(passive_text_pl(**definition["passive_override"]) if "passive_override" in definition else class_passive_text_pl(passive_parent))}.')
        CLASS_STARTING_STAT_BONUSES[name]=copy.deepcopy(base['stat_bonuses'][parent])
        AUTHORED_CLASS_PASSIVE_PROFILES[name]=copy.deepcopy(definition.get('passive_override',base['passives'][passive_parent]))
        cloned=[]
        for source_skill in base['skills'][skill_parent]:
            row=copy.deepcopy(source_skill)
            row['id']='v7700_'+slug+'_'+source_skill['id']
            row['name']=name+': '+str(source_skill['name'])
            row['aliases']=[row['name'].lower()]
            row['natural_tags']=[name.lower(),skill_parent.lower()]
            if row.get('mastery_choice_group'):
                row['mastery_choice_group']=name+':'+str(row.get('unlock',1))
            row['desc']=(f'Umiejetnosc klasy {name} oparta na mechanice {skill_parent}. '+
                         str(source_skill.get('desc','')))
            cloned.append(row)
        CLASS_SKILLS[name]=cloned
def restore():_apply(current())
def rebase_after_heritage():
    global _ORIGINAL
    previous=_base()
    changed=copy.deepcopy(previous)
    count=len(previous['classes'])
    changed['classes']=tuple(copy.deepcopy(CLASSES[:count]))
    # Rebuild only the original class baseline, never copy custom skill sets.
    _ORIGINAL=changed
    _apply(current())
def inherited_parent(class_name):
    # May be used for locating the corresponding guild trainer.
    return current().get(class_name,{}).get('parent')
