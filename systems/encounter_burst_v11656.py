# -*- coding: utf-8 -*-
"""Read-only, cached skill-burst forecast for level-appropriate encounters.

Unlike autoattack-only DPS, this includes actually learned offensive skills.
No damage/experience/level is changed and no skill is executed.  Published
skill combo helpers are stateful: do NOT call their mutating forecast path.
"""
from __future__ import annotations

import time

OFFENSIVE_KINDS = frozenset(('damage', 'aoe_damage', 'execute', 'drain'))
MEC_BRANCHES = frozenset(('melee', 'ranged', 'feedback', 'magic'))


def member_skill_burst_v11656(member, *, now=None):
    """Return approximate strongest single offensive skill, or zero if none.

    Caches one DB snapshot for twelve seconds to keep combat hot paths fast.
    Only known skills from the player's currently active class are considered;
    inactive/locked skills do not boost the enemy's health.
    """
    now = time.monotonic() if now is None else float(now)
    char = getattr(member, 'character', None)
    db = getattr(getattr(member, 'server', None), 'db', None)
    if char is None or db is None:
        return 0
    cache_key = (int(getattr(char, 'character_level', 1) or 1),
                 int(getattr(char, 'soul_level', 1) or 1),
                 str(getattr(char, 'class_name', '')))
    cached = getattr(member, '_burst_forecast_v11656', None)
    if cached and cached[0] == cache_key and now - cached[1] < 12.0:
        return cached[2]
    from core.progression_resources import skill_power_multiplier
    from systems.soul_ancients_v1330 import evolution_power_multiplier
    from systems.soul_evolutions_v1332 import role_evolution
    from systems.published_28_expansion import ACTIVE as skill_bonus_rules

    try:
        known = set(db.learned_skill_ids(member.account_id))
        skills = tuple(member.class_skills())
    except (AttributeError, TypeError, ValueError):
        return 0
    strongest = 0
    for skill in skills:
        if not isinstance(skill, dict) or skill.get('kind') not in OFFENSIVE_KINDS:
            continue
        skill_id = str(skill.get('id', ''))
        if not skill_id or skill_id not in known:
            continue
        # Compress is an exact percentage of current target HP, not an
        # Attack*multiplier skill. It must never set an independent HP floor.
        if skill.get('mec_special') == 'compress':
            continue
        try:
            progress = db.skill_progress(member.account_id, skill_id)
            level = max(1, int(progress['level']))
            soul = max(1, int(char.soul_level))
            role = 'offense'
            skill_factor = (skill_power_multiplier(level)
                            * evolution_power_multiplier(level, soul)
                            * role_evolution(skill, level, soul, role))
            core = int(member.offensive_skill_core_power_v11185(skill))
            kind = member.offensive_skill_damage_type_v11190(skill)
            # Mec Feedback's direct HP contribution is part of the real
            # first hit, but was absent from the v116.56 forecast. Never
            # mutate HP or consume a skill merely to estimate its power.
            special = str(skill.get('mec_special', '') or '')
            if special in ('robo_tackle', 'kamikaze_crush'):
                from decimal import Decimal, ROUND_HALF_UP
                health = max(0, int(getattr(member, 'current_hp', 0) or 0))
                ratio = Decimal(str(skill.get('current_hp_power_ratio',
                    0.20 if special == 'kamikaze_crush' else 0.12) or 0))
                core += int((Decimal(health) * ratio).to_integral_value(
                    rounding=ROUND_HALF_UP))
            c = char
            core = max(1, int(core))
            mult = float(skill.get('mult', 1.0) or 1.0)
            if kind == 'physical':
                mult *= c.class_physical_damage_multiplier() * c.racial_physical_damage_multiplier()
            elif kind == 'magic':
                mult *= c.class_magic_damage_multiplier() * c.racial_magic_damage_multiplier()
            mult *= c.racial_all_damage_multiplier()
            mult *= member.total_set_damage_multiplier()
            mult *= member.equipment_damage_multiplier(kind)
            mult *= member.skill_buff_multiplier(target_type=kind)
            from systems.party_synergies import party_synergy_damage_multiplier_v11338
            mult *= party_synergy_damage_multiplier_v11338(member, kind)
            mult *= skill_bonus_rules['skills'].get('global', {}).get('damage_percent', 100) / 100.0
            if skill.get('mec_authored') and skill.get('mec_branch') in MEC_BRANCHES:
                mult *= member.mec_branch_multiplier_v0319(
                    str(skill['mec_branch']), str(skill.get('mec_special', '')))
            # Combo / chain / alternation multiply live hits but their
            # helpers also CHANGE session state. Inspect only published
            # metadata, and use the strongest legal conditional factor.
            from systems.published_32_finale import ACTIVE as combo_rules
            from systems.published_33_mechanics import ACTIVE as alternate_rules
            from systems.published_34_integration import ACTIVE as chain_rules
            for rules, field in ((combo_rules, 'combo_percent'),
                                 (alternate_rules, 'bonus_percent'),
                                 (chain_rules, 'bonus_percent')):
                row = rules.get('skills', {}).get(skill_id, {})
                mult *= max(1.0, float(row.get(field, 100) or 100) / 100.0)
            # Max crit is possible on first contact. This forecast is a
            # target for roughly two rotations, not a guarantee of exact RNG.
            crit = max(1.0, float(member.critical_multiplier()))
            if core.bit_length() > 900:
                # Never discard a trained high-tier skill as a bogus zero
                # simply because float(int) exceeds IEEE-754's range.
                from core.large_number_math import rounded_product
                expected = max(0, rounded_product(core, skill_factor, mult, crit))
            else:
                expected = max(0, int(core * skill_factor * mult * crit))
            strongest = max(strongest, expected)
        except (ArithmeticError, AttributeError, KeyError, TypeError, ValueError):
            # A single exotic skill must not break any real combat.
            continue
    member._burst_forecast_v11656 = (cache_key, now, strongest)
    return strongest


def party_skill_burst_v11656(members, *, now=None):
    """A single first rotation of learned skills from real party members."""
    return sum(member_skill_burst_v11656(member, now=now) for member in members)
