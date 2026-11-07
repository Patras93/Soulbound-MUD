# -*- coding: utf-8 -*-
"""v106 staging: real Soul Level as *threat-comparison* level in new realms.

This never changes character_level, abilities, actual damage, XP, equipment,
Admin Live limits or monster authored HP. For all historical v105 fights,
non-v106 rooms, missing context, or production, returns historical level.
"""
from __future__ import annotations
import os


def effective_encounter_level_v106(character, mob, template=None, room=None):
    """Return a bounded level for adaptive HP/incoming/consider only.

    The level is max(character level, Soul Level) on AUTHORED v106 mobs in
    v106 rooms with the 30001+ region label. A beginner without Soul Level
    receives no shortcut; all underlevel pressure is preserved.
    """
    def level(value):
        if isinstance(value, bool):
            return 1
        try:
            return max(1, int(value or 1))
        except (ValueError, TypeError, OverflowError):
            return 1

    legacy=level(getattr(character, 'character_level', 1))
    if os.environ.get('SOULBOUND_V106_STAGING') != '1':
        return legacy
    mob_id=str(getattr(mob, 'template_id', '') or '')
    room_id=str(getattr(mob, 'room_id', '') or '')
    if not (mob_id.startswith('v10600_') and room_id.startswith('v10600_')):
        return legacy
    if not isinstance(template, dict) or not isinstance(room, dict):
        return legacy
    # Guard against similarly named but unrelated/training templates and
    # low-level test rooms. Never allow a copied name to bypass a real stage.
    if template.get('training_dummy') or room.get('training_dummy'):
        return legacy
    if level(room.get('generator_level', 1)) < 30001:
        return legacy
    stage=max(level(room.get('generator_level', 1)),
              level(template.get('v106_authored_boss_stage', 1)),
              level(template.get('generator_level', 1)))
    if stage < 30001:
        return legacy
    soul=level(getattr(character, 'soul_level', 1))
    if soul >= stage:
        return max(legacy, soul)
    # Historical level-disadvantage grows by ABSOLUTE level gaps. At level
    # 30000, even a one-region difference (e.g. 699 levels) previously
    # multiplied HP thousands of times. Compare proportional progress within
    # the 600-level legacy pressure scale: gap of 1% ~= six levels. This
    # changes only the level passed into threat *comparisons*, not the true
    # enemy stage, authored HP, player damage, rewards or unlock requirements.
    gap=stage-soul
    proportional_gap=min(600, max(1, (gap*600+stage-1)//stage))
    return max(legacy, stage-proportional_gap)
