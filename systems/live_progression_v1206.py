# -*- coding: utf-8 -*-
"""Validated live EXP rule state, v12.00.6. No code is loaded from JSON."""
PROFESSION_XP_PERCENT = {}
PROFESSION_XP_SCALE = {}
TOOL_XP_SCALE = {}
TOOL_XP_PERCENT = {}
RESOURCE_XP_RULES = {}


def install(professions, tools, resources=None):
    PROFESSION_XP_PERCENT.clear()
    PROFESSION_XP_SCALE.clear()
    TOOL_XP_SCALE.clear()
    TOOL_XP_PERCENT.clear()
    RESOURCE_XP_RULES.clear()
    RESOURCE_XP_RULES.update({key: dict(value) for key, value in (resources or {}).items()})
    PROFESSION_XP_PERCENT.update({key: value['xp_percent'] for key, value in professions.items() if 'xp_percent' in value})
    TOOL_XP_PERCENT.update({key: value['xp_percent'] for key, value in tools.items() if 'xp_percent' in value})
    PROFESSION_XP_SCALE.update({key: value['xp_scale'] for key, value in professions.items() if 'xp_scale' in value})
    TOOL_XP_SCALE.update({key: value['xp_scale'] for key, value in tools.items() if 'xp_scale' in value})


def xp_with_live_bonus(value, key, *, tool=False):
    """Preserve every prior positive payout as a floor; never create XP from zero."""
    old = max(0, int(value or 0))
    if not old:
        return old
    scale = (TOOL_XP_SCALE if tool else PROFESSION_XP_SCALE).get(key)
    if scale is not None:
        return (old * int(scale) + 50) // 100
    percent = (TOOL_XP_PERCENT if tool else PROFESSION_XP_PERCENT).get(key, 100)
    return max(old, (old * int(percent) + 50) // 100)


def resource_rule_xp(previous, item_id, *, tool=False):
    """Apply a checked, monotonic per-material rule after tier-based EXP.

    Fixed XP is a minimum before subsequent guild/event bonuses and EXP bank;
    never promise an exact final payout for every player. Rare variants may
    inherit their base resource's rule, unless they have their own override.
    """
    old = max(0, int(previous or 0))
    if not item_id:
        return old
    rule = RESOURCE_XP_RULES.get(str(item_id))
    if rule is None:
        from data.items import ITEMS
        item = ITEMS.get(str(item_id), {})
        base = item.get('base_resource_id') if isinstance(item, dict) else None
        if base and base != item_id:
            rule = RESOURCE_XP_RULES.get(str(base))
    if not rule:
        return old
    side = 'tool' if tool else 'prof'
    mode = rule.get(side + '_mode')
    if mode == 'auto':
        return old
    if mode == 'manual':
        return max(0, int(rule[side + '_fixed']))
    if mode == 'percent':
        return (old * int(rule[side + '_scale']) + 50) // 100
    # Legacy v12.00.7 rules retain the pre-existing minimum semantics.
    if old == 0:
        return old
    factor = int(rule.get('tool_percent' if tool else 'prof_percent', 100))
    floor = int(rule.get('tool_xp' if tool else 'prof_xp', 0))
    return max(old, (old * factor + 50) // 100, floor)
