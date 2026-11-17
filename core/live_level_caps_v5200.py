# -*- coding: utf-8 -*-
"""Immutable deployment-time growth policy, legacy import compatibility only.

The game has no interactive configuration editor, cap file or live switch.
All nine progression tracks are unbounded. Equipment improvement is +10.
The technical ceiling is a compatibility value used by old algorithms;
it is NOT a configurable player-level restriction.
"""
from __future__ import annotations
import sys

TECHNICAL_CEILING=1_000_000_000
PROGRESSION_KEYS=('postac','bieglosc','dusza','bron_duszy','skille','profesje','narzedzia','gildia','eq')
KEYS=PROGRESSION_KEYS+('ulepszenia_eq',)
DEFAULTS=dict.fromkeys(PROGRESSION_KEYS,None)
DEFAULTS['ulepszenia_eq']=10
_state=dict(DEFAULTS)
_loaded=True
ALIASES={'character':'postac','level':'postac','klasa':'bieglosc','klasy':'bieglosc',
         'soul':'dusza','bron':'bron_duszy','skill':'skille','profesja':'profesje',
         'narzedzie':'narzedzia','guild':'gildia','eq_plus':'ulepszenia_eq'}
GLOBAL_NAMES={
    'CHARACTER_MAX_LEVEL':'postac','CLASS_MASTERY_MAX_LEVEL':'bieglosc',
    'SOUL_MAX_LEVEL':'dusza','SOUL_WEAPON_MASTERY_MAX_LEVEL':'bron_duszy',
    'SKILL_MAX_LEVEL':'skille','PROFESSION_MAX_LEVEL':'profesje',
    'BLACKSMITHING_MAX_LEVEL':'profesje','JEWELCRAFTING_MAX_LEVEL':'profesje',
    'TOOL_MAX_LEVEL':'narzedzia','V0926_GUILD_MAX_LEVEL':'gildia',
    'EQUIPMENT_MAX_LEVEL':'eq','V03042_EQ_UPGRADE_MAX':'ulepszenia_eq',
}
MODULE_PREFIXES=('core.','config.','player.','storage.','world.','network.','systems.')

def normalize_key(value):
    key=str(value or '').strip().lower().replace('-','_')
    key=ALIASES.get(key,key)
    if key not in KEYS:raise ValueError('Nieznana dziedzina rozwoju.')
    return key

def current():return dict(_state)
def cap(kind):return _state[normalize_key(kind)]
def can_grow(kind,level):
    value=cap(kind)
    return value is None or int(level)<value

def effective_number(value):return TECHNICAL_CEILING if value is None else int(value)
def display(value):return 'bez limitu' if value is None else str(int(value))

def _apply_to_runtime():
    numbers={name:effective_number(_state[axis]) for name,axis in GLOBAL_NAMES.items()}
    for name,mod in tuple(sys.modules.items()):
        if mod is None:continue
        host=(name in ('server','__main__') and
              str(getattr(mod,'__file__','')).replace('\\','/').endswith('/server.py'))
        if not (name.startswith(MODULE_PREFIXES) or host):continue
        for symbol,value in numbers.items():
            if type(vars(mod).get(symbol)) is int:setattr(mod,symbol,value)
    infinite=sys.modules.get('systems.infinite_equipment')
    if infinite is not None:
        update=getattr(infinite,'refresh_infinite_equipment_requirements_v5300',None)
        if callable(update):update()
