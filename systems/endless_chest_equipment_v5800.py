# -*- coding: utf-8 -*-
"""v58: one additional ordinary EQ opportunity per eligible high-floor boss chest.

Existing authored chest rolls (potions/gems/soul fragments), keys, ownership,
recipients and rewards are unchanged. This extra chance is opt-in by depth only:
no roll at/below stage 800. The new item comes from eight non-UOSS armor bases,
uses the existing durable Rezonans Glebi ID scheme and is awarded per recipient.
"""
from __future__ import annotations
import random
from data.items import ITEMS
from systems.infinite_equipment import infinite_source_profile, infinite_equipment_variant_for_drop
from systems.endless_loot_v5600 import eligible_normal_equipment_drop_v5600

# Only source types with an implemented physical boss chest in the world.
_FLOOR_FIELDS = {'crypt':'crypt_floor', 'mythic_crypt':'mythic_crypt_floor',
                 'astral':'astral_floor', 'mythic_astral':'mythic_astral_floor'}
_ALIASES={'krypta':'crypt','mityczna_krypta':'mythic_crypt',
          'wieza':'astral','astral':'astral',
          'mityczna_wieza':'mythic_astral','mityczny_astral':'mythic_astral',
          **{k:k for k in _FLOOR_FIELDS}}
_BASE_ITEMS=('leather_vest','iron_helmet','iron_guard','iron_gauntlets',
             'iron_leggings','iron_boots','forge_charm','lucky_charm')
# Fixed and documented: 1 extra EQ at most, chance per eligible recipient.
_CHANCE_NUM=25
_CHANCE_DEN=100


def _chest_template(kind,floor):
    key=_FLOOR_FIELDS.get(str(kind or '').lower())
    if key is None or isinstance(floor,bool):return None
    try:
        f=int(floor)
    except (ValueError,TypeError,OverflowError):return None
    if f<1 or f>1_000_000:return None
    return {key:f,'boss':True}


def chest_equipment_profile_v5800(kind,floor):
    template=_chest_template(kind,floor)
    profile=infinite_source_profile(template) if template else None
    if profile is None or profile['effective_stage']<=800:return None
    return {'template':template,'profile':profile,'chance':_CHANCE_NUM}


def enhance_boss_chest_equipment_v5800(kind,floor,reward,*,rng=None):
    """Run after original chest roll and v57 gold extension; no more than one EQ.

    Under normal gameplay the RNG is the same source as authored chest rolls.
    Tests inject a deterministic RNG; ineligible sources consume no randomness.
    """
    if not isinstance(reward,dict) or not isinstance(reward.get('items'),list):return reward
    setup=chest_equipment_profile_v5800(kind,floor)
    if setup is None:return reward
    generator = rng if rng is not None else random
    if generator.random()>=_CHANCE_NUM/_CHANCE_DEN:return reward
    candidates=[item for item in _BASE_ITEMS
                if eligible_normal_equipment_drop_v5600(item,setup['template'])]
    if not candidates:return reward
    chosen=generator.choice(candidates)
    item_id=infinite_equipment_variant_for_drop(chosen,setup['template'])
    if item_id==chosen or item_id not in ITEMS:return reward
    result=dict(reward)
    result['items']=list(reward['items'])+[item_id]
    return result


def preview_chest_equipment_v5800(kind,floor):
    normalized=_ALIASES.get(str(kind or '').lower())
    if not normalized:raise ValueError('Zrodlo: krypta, mityczna_krypta, wieza, mityczna_wieza.')
    raw=str(floor or '')
    if not raw.isascii() or not raw.isdecimal() or len(raw)>7 or not 1<=int(raw)<=1_000_000:
        raise ValueError('Pietro: podaj liczbe 1..1000000.')
    setup=chest_equipment_profile_v5800(normalized,int(raw))
    if setup is None:
        return 'SKRZYNIA EQ: ponizej etapu 801 bonus EQ nie jest losowany. Stare nagrody bez zmian. Tylko podglad.'
    p=setup['profile']
    from core.equipment_growth_v5300 import infinite_equipment_requirement
    return (f'SKRZYNIA EQ: {normalized} pietro {int(raw)}, etap {p["effective_stage"]}, '
            f'wymagana bieglosc {infinite_equipment_requirement(p["effective_stage"])}, '
            f'szansa {_CHANCE_NUM}%, maksymalnie jeden bonusowy pancerz lub talizman na gracza. '
            'Bez dodatkowego losowania w podgladzie; istniejace nagrody i klucze bez zmian.')
