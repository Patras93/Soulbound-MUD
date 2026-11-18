# -*- coding: utf-8 -*-
"""v115 deterministic quest/achievement definitions.

These are catalog definitions, not yet connected to gameplay kill/event hooks,
loot, world spawns or progression claims. No soundpack imports.
"""
from __future__ import annotations
from dataclasses import dataclass
from .high_level_world import REGIONS

OBJECTIVES=('defeat_enemy','defeat_boss','explore','complete_quest','collect_resource',
            'craft_item','discover_checkpoint','finish_dungeon','help_party','win_challenge')

@dataclass(frozen=True)
class Quest:
    key: str
    region: str
    objective: str
    target: int
    tier: int
    title: str

@dataclass(frozen=True)
class Achievement:
    key: str
    region: str
    objective: str
    threshold: int
    tier: int
    title: str
    repeatable: bool


def quest_catalog():
    """5000 distinct authored-pattern progression definitions: 30 regions, 10 goals."""
    result=[]
    for i in range(5000):
        region=REGIONS[i%len(REGIONS)]
        objective=OBJECTIVES[(i//len(REGIONS))%len(OBJECTIVES)]
        tier=i//(len(REGIONS)*len(OBJECTIVES))+1
        target=max(1,tier*({
            'defeat_enemy':10, 'defeat_boss':1, 'explore':3,
            'complete_quest':2, 'collect_resource':5,'craft_item':2,
            'discover_checkpoint':1,'finish_dungeon':1,
            'help_party':2,'win_challenge':1}[objective]))
        result.append(Quest(f'v115_quest_{i+1:05d}',region.key,objective,target,tier,
                            f'{region.name}: {objective} — próba {tier}'))
    return tuple(result)


def achievement_catalog():
    result=[]
    for i in range(2000):
        region=REGIONS[i%len(REGIONS)]
        objective=OBJECTIVES[(i//len(REGIONS))%len(OBJECTIVES)]
        tier=i//(len(REGIONS)*len(OBJECTIVES))+1
        result.append(Achievement(f'v115_achievement_{i+1:05d}',region.key,
                                  objective,tier*(10 if objective=='defeat_enemy' else 1),
                                  tier,f'{region.name}: mistrzostwo {objective} {tier}',True))
    return tuple(result)


def repeatable_threshold(base: int, cycle: int):
    """Require increasing progress for repeatable mastery, never overflow int64."""
    if isinstance(cycle,bool) or not isinstance(cycle,int) or cycle<0 or cycle>1_000_000:
        raise ValueError('Nieprawidłowy cykl')
    if not isinstance(base,int) or base<1:raise ValueError('Nieprawidłowy próg')
    return base*(cycle+1)
