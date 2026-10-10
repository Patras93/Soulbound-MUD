# -*- coding: utf-8 -*-
"""Soulbound v1.40.5: slow out-of-combat HP regeneration, no free instant resets.

Pure integer arithmetic works for very large endgame boss health pools.
"""

REGEN_PERCENT_PER_TICK_V1405 = 10
REGEN_TICK_SECONDS_V1405 = 15


def preserve_hp_when_encounter_ends_v1405(hp, old_max_hp, base_max_hp):
    """Discard adaptive scaling but retain battle damage as the HP fraction."""
    base = max(1, int(base_max_hp))
    previous = max(base, int(old_max_hp))
    surviving = min(previous, max(0, int(hp)))
    if surviving <= 0:
        return 0
    return max(1, min(base, (base * surviving + previous - 1) // previous))


def restore_idle_hp_tick_v1405(mob, template):
    """Heal an idle living enemy by up to 10% template HP per 15-second tick.

    Engagement is enforced by caller and checked here too. Never revive dead
    mobs, heal monsters still fighting or change an adaptive encounter's max HP.
    """
    if (not getattr(mob, 'alive', False) or int(getattr(mob, 'hp', 0)) <= 0
            or getattr(mob, 'engaged_by', None)
            or getattr(mob, 'aoe_engaged_by', None)
            or int(getattr(mob, 'adaptive_max_hp_v11330', 0) or 0) > 0):
        return 0
    maximum = max(1, int((template or {}).get('max_hp', 1) or 1))
    current = int(mob.hp)
    if current >= maximum:
        return 0
    amount = min(maximum - current,
                 max(1, (maximum * REGEN_PERCENT_PER_TICK_V1405 + 99) // 100))
    mob.hp = current + amount
    return amount
