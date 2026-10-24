# -*- coding: utf-8 -*-
"""v55: post-800 crafted equipment progression.

Never changes recipes, resources, quality rolls, earned profession EXP, nor
players' databases. Result ID is self-describing and restored by the existing
deepq loader on restart. Only activated by explicit admin EQ progression caps.
"""
from __future__ import annotations
import math
from core import live_level_caps_v5200 as caps
from data.items import ITEMS
from systems.infinite_equipment import register_infinite_equipment_variant


def craft_stage_v5500(profession_level, tool_level):
    """Both real profession and tool mastery must be above 800."""
    try:
        profession=int(profession_level)
        tool=int(tool_level)
    except (ValueError,TypeError,OverflowError):
        return None
    if profession<=800 or tool<=800 or caps.effective_number(caps.cap('eq'))<=800:
        return None
    # A top-heavy profession cannot bypass its underlevelled tool.
    source=min(profession, tool)
    source=min(source,caps.effective_number(caps.cap('eq')))
    if source<=800:return None
    return min(1_000_000_000, ((source+9)//10)*10)


def endless_crafted_equipment_v5500(item_id, profession_level, tool_level):
    stage=craft_stage_v5500(profession_level,tool_level)
    if stage is None:return item_id
    item=ITEMS.get(item_id)
    if not isinstance(item,dict) or str(item_id).startswith(('deepq_','uoss_')) or item.get('fur_shop_token') or item.get('uoss_unique'):
        return item_id
    if item.get('type') not in ('armor','weapon','equipment') and not item.get('slot'):
        return item_id
    # Preserve the existing quality/critical craft suffix in nested base ID.
    grade='e' if item.get('craft_quality_v03054') in ('masterwork','legendary') else 'r'
    rank=(stage-600)//10
    return register_infinite_equipment_variant(item_id,'forge',grade,rank)
