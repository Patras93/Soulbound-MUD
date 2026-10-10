# -*- coding: utf-8 -*-
"""Soulbound mage elementals: four elements with lesser, normal and greater forms.

Inspired by Alter Aeon's elemental summoning, with independent Soulbound balance.
One instance per kind is retained by the existing durable summons_v1700 table.
"""
from __future__ import annotations

ELEMENTS={
    'ogien': ('Ognia', ((65,.39,1),(100,.63,2),(145,.86,3))),
    'blyskawice': ('Błyskawic', ((75,.55,2),(115,.84,3),(165,1.16,4))),
    'lod': ('Lodu', ((85,.24,1),(127,.37,2),(185,.52,3))),
    'krysztal': ('Kryształu', ((110,.30,2),(160,.45,3),(210,.64,4))),
}
RANKS=('mniejszy','zwykly','potezny')
LABELS=('Mniejszy','', 'Potężny')
ELEMENTALS={}
for element,(name,levels) in ELEMENTS.items():
    for i,(mana,damage,upkeep) in enumerate(levels):
        key=f'zywiolak_{element}_{RANKS[i]}'
        label=f'{LABELS[i]} Żywiołak {name}'.strip()
        ELEMENTALS[key]={'element':element,'rank':i,'mana':mana,'damage':damage,'upkeep':upkeep,'name':label}

ELEMENT_ALIASES={
    'ogien':'ogien','ognia':'ogien','fire':'ogien',
    'blyskawica':'blyskawice','blyskawic':'blyskawice','blyskawice':'blyskawice','piorun':'blyskawice','pioruny':'blyskawice','lightning':'blyskawice',
    'lod':'lod','lodu':'lod','ice':'lod',
    'krysztal':'krysztal','krysztalu':'krysztal','crystal':'krysztal',
}
RANK_ALIASES={'maly':0,'mniejszy':0,'slaby':0,'lesser':0,'normalny':1,'zwykly':1,'sredni':1,'normal':1,'duzy':2,'potezny':2,'wiekszy':2,'greater':2}

def resolve_elemental(args):
    """Resolve e.g. ogien potezny, lod, crystal lesser, without hidden defaults."""
    if not args:return None
    name=ELEMENT_ALIASES.get(args[0])
    if name is None:return None
    if len(args)>2:return None
    rank=RANK_ALIASES.get(args[1]) if len(args)>1 else 1
    if rank is None:return None
    key=f'zywiolak_{name}_{RANKS[rank]}'
    return key if key in ELEMENTALS else None
