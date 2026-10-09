# -*- coding: utf-8 -*-
"""Class-skill evolutions by authored identity, without mutating saved skill rows.

The v1.33.0 universal skill-power multiplier remains intact.  This module
adds *role-specific* evolution effects to existing, learned abilities.
"""
from systems.soul_ancients_v1330 import evolution_stage

ROLE_LABELS = {
    "damage": "Przebicie", "aoe_damage": "Rozmach", "execute": "Wyrok",
    "drain": "Wysysanie", "heal": "Łaska", "group_heal": "Harmonia",
    "regen": "Odnowa", "guard": "Bastion", "boost": "Inspiracja",
    "evade": "Zwinność", "passive": "Instynkt", "utility": "Rzemiosło",
}

def skill_role(skill):
    return str((skill or {}).get("kind", "utility"))

def role_evolution(skill, skill_level, soul_level, effect):
    """Non-random modifier; no cooldown, XP or stat caps.  Default is neutral.

    Each skill keeps its own name, school and target rules.  Effects apply
    only to an appropriate existing mechanic (never convert heals to attacks).
    """
    stage = evolution_stage(skill_level, soul_level)
    role = skill_role(skill)
    amounts = {
        "offense": {"damage": .025, "aoe_damage": .020, "execute": .030, "drain": .015},
        "healing": {"heal": .04, "group_heal": .05},
        "guard": {"guard": .06},
        "regen_tick": {"regen": .08},
        "regen_duration": {"regen": .05},
        "passive_boost": {"boost": .04},
        "protocol": {"passive": .025},
    }
    return 1.0 + stage * amounts.get(effect, {}).get(role, 0.0)

def evolution_description(skill, skill_level, soul_level):
    role = skill_role(skill)
    stage = evolution_stage(skill_level, soul_level)
    label = ROLE_LABELS.get(role, "Technika")
    effect = {
        "damage": "siła ciosu", "aoe_damage": "siła ataku obszarowego",
        "execute": "siła ciosu kończącego", "drain": "siła ataku wysysającego",
        "heal": "skuteczność leczenia", "group_heal": "leczenie drużyny",
        "regen": "siła i czas regeneracji", "guard": "ochrona drużyny",
        "boost": "pasywne wzmocnienie", "evade": "unik dla drużyny",
        "passive": "działanie istniejącej pasywki", "utility": "istniejąca technika",
    }.get(role, "efekt")
    return f"{label}, etap {stage}/3 — {effect}"

def council_allies(mobs, room_id, exclude=None):
    """Living authored Ancients in the *same* arena, never across rooms."""
    if room_id != "v1332_ancients_council_arena":
        return []
    return [m for m in mobs if m is not exclude and getattr(m, "alive", False)
            and getattr(m, "room_id", None) == room_id
            and str(getattr(m, "template_id", "")).split('__', 1)[0] in (
                "v1310_anc_deep_boss", "v1310_anc_sky_boss",
                "v1310_anc_lost_boss", "v1310_anc_orc_boss")]

def audit():
    from core.classes_skills import CLASS_SKILLS
    skills = [skill for ls in CLASS_SKILLS.values() for skill in ls]
    assert len(skills) > 1000
    for skill in skills:
        assert role_evolution(skill, 1, 800, "offense") == 1.0
        assert role_evolution(skill, 800, 800, "offense") >= 1.0
    assert role_evolution({"kind":"heal"}, 600,600,"healing") > 1.0
    assert role_evolution({"kind":"guard"},600,600,"guard") > 1.0
    assert role_evolution({"kind":"regen"},600,600,"regen_tick") > 1.0
    assert role_evolution({"kind":"boost"},600,600,"passive_boost") > 1.0
    return {"skills":len(skills), "roles":len(ROLE_LABELS)}
