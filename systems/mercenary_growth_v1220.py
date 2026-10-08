# -*- coding: utf-8 -*-
"""Mercenary tactics. Mercenaries follow the owner, without XP or talent tiers."""
from math import isqrt

TACTICS = {
    "automatyczna": "Automatyczna: własne umiejętności najemnika, bez dodatkowego bonusu",
    "szturm": "Szturm: mocniejszy atak, bez dodatkowej osłony i leczenia",
    "obrona": "Obrona: dodatkowa osłona rannego lub zagrożonego członka drużyny",
    "wsparcie": "Wsparcie: dodatkowe leczenie rannych członków drużyny",
}
# Old specialization values are treated as a chosen tactic, not progression.
SPECIALIZATIONS = TACTICS

def mercenary_owner_level_v1228(character):
    return max(1, int(getattr(character, "character_level", 1) or 1))

# Historical helpers retained for import compatibility; not used to level hires.
def mercenary_level(xp):
    return 1 + isqrt(max(0, int(xp)) // 180)

def mercenary_xp_for_level(level):
    return 180 * max(0, int(level) - 1) ** 2

def mercenary_action_xp(owner_level, foe_level, boss=False):
    enemy = max(1, int(foe_level)); owner = max(1, int(owner_level))
    return min(2500, 18 + enemy // 3 + min(owner, enemy) // 6 + (enemy // 4 if boss else 0))

def mercenary_tactic(stored):
    return str(stored or "automatyczna") if str(stored or "automatyczna") in TACTICS else "automatyczna"

def mercenary_attack_multiplier(level, tactic):
    # Level follows owner; no talent milestones or separately earned bonuses.
    bonus = min(0.20, max(0, int(level) - 1) * 0.002)
    if mercenary_tactic(tactic) == "szturm":
        bonus += 0.08
    return 1.0 + bonus

def mercenary_unlocked(level, tactic):
    """Legacy API used by old status tests, now reports the selected tactic."""
    return "Taktyka " + mercenary_tactic(tactic)
