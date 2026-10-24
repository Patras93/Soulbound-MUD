# -*- coding: utf-8 -*-
"""Bounded owner-authored values for existing race/class passive kinds.
No user Python, no arbitrary scripts and no new unsupported passive category.
A custom passive may be chosen only at the creation of a new playable archetype.
"""
from __future__ import annotations
import re
from core.character_resources import AUTHORED_RACE_PASSIVE_PROFILES, AUTHORED_CLASS_PASSIVE_PROFILES


def _allowed():
    limits={}
    for profile in list(AUTHORED_RACE_PASSIVE_PROFILES.values())+list(AUTHORED_CLASS_PASSIVE_PROFILES.values()):
        kind=str(profile['kind']); val=float(profile['value'])
        limits[kind]=max(limits.get(kind,0),val)
    return limits


def parse_profile(kind,percentage):
    limits=_allowed()
    if kind not in limits:raise ValueError('Nieobslugiwany pasyw. Dozwolone: '+', '.join(sorted(limits)))
    if not isinstance(percentage,str) or re.fullmatch(r'\d{1,2}(?:\.\d{1,2})?',percentage,re.ASCII) is None:
        raise ValueError('Pasyw: procent podaj jako liczbe 0.01..maksimum bazowe, np. 8 lub 2.5.')
    value=round(float(percentage)/100,4)
    if not 0.0001<=value<=limits[kind]+1e-10:
        raise ValueError(f'Pasyw {kind}: maksymalnie {limits[kind]*100:g} procent zgodnie z istniejacymi archetypami.')
    return {'kind':kind,'value':value}


def validate_profile(value):
    if type(value) is not dict or set(value)!={'kind','value'}:
        raise ValueError('Pasyw: wymagane tylko kind i value.')
    kind=value['kind'];num=value['value']
    if type(kind) is not str or type(num) not in (int,float):
        raise ValueError('Pasyw: niepoprawny typ rodzaju lub mocy.')
    from decimal import Decimal
    if not 0 < Decimal(str(num)) <= Decimal(str(_allowed().get(kind,0))):
        raise ValueError('Pasyw: moc wykracza poza sprawdzony zakres bazowy.')
    # Keep serialization exact and deterministic across platforms.
    if round(float(num),4)!=float(num):
        raise ValueError('Pasyw: dokladnosc do czterech miejsc dziesietnych.')
    return {'kind':kind,'value':float(num)}
