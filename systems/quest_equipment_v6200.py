# -*- coding: utf-8 -*-
"""Quest-authored equipment after 800: same authored reward count, stable gear ID.

Only explicitly high-level quests generate Rezonans Głębi; simply being a
high-level player must never turn a repeatable beginner quest into high gear.
No RNG, database, NPC or quest-state access. Unique UOSS rewards excluded.
"""
from __future__ import annotations
from data.items import ITEMS
from systems.infinite_equipment import (
    infinite_equipment_variant_for_drop, infinite_source_profile,
    infinite_equipment_variant_id, infinite_equipment_power_multiplier,
)
from core.equipment_growth_v5300 import infinite_equipment_requirement

_FIELDS=('generator_level','recommended_level','required_mastery','level')


def quest_gear_stage_v6200(quest):
    if not isinstance(quest,dict) or any(quest.get(k) for k in ('uoss_superboss','uoss_superboss_id','uoss_unique')):
        return None
    stages=[]
    for key in _FIELDS:
        raw=quest.get(key)
        if isinstance(raw,bool):continue
        try:level=int(raw or 0)
        except (ValueError,TypeError,OverflowError):continue
        if 801<=level<=1_000_000_000:stages.append(level)
    return max(stages) if stages else None


def quest_gear_profile_v6200(item_id,quest):
    item=ITEMS.get(str(item_id or ''))
    if (not isinstance(item,dict) or str(item_id).startswith(('deepq_','uoss_'))
        or item.get('uoss_unique') or item.get('uoss_superboss') or item.get('uoss_superboss_id') or item.get('fur_shop_token')
        or (item.get('type') not in ('armor','weapon','equipment') and not item.get('slot'))):
        return None
    stage=quest_gear_stage_v6200(quest)
    if stage is None:return None
    # Map quest level into the same validated continuation curve as world EQ.
    source=infinite_source_profile({'level':stage})
    if source is None:return None
    return dict(source,source='quest')


def quest_equipment_id_v6200(item_id,quest):
    profile=quest_gear_profile_v6200(item_id,quest)
    if not profile:return str(item_id)
    from systems.infinite_equipment import register_infinite_equipment_variant
    return register_infinite_equipment_variant(item_id,'quest','r',profile['rank'])


def preview_quest_equipment_v6200(item_id,quest):
    stage=quest_gear_stage_v6200(quest)
    if stage is None:
        return 'EQ QUEST: zadanie nie ma jawnego etapu ponad 800. Nagrody bez zmian.'
    profile=quest_gear_profile_v6200(item_id,quest)
    if profile is None:
        return 'EQ QUEST: przedmiot nie jest zwyklym EQ albo jest unikatowy. Bez zmian.'
    rank=profile['rank'];eff=profile['effective_stage']
    vid=infinite_equipment_variant_id(str(item_id),'quest','r',rank)
    return (f'EQ QUEST: etap {stage}, Rezonans {rank}, moc x{infinite_equipment_power_multiplier(rank):.3f}, '
            f'biegłość {infinite_equipment_requirement(eff)}, ID {vid}. '
            'Tylko podglad. Ilosc nagrod bez zmian.')
