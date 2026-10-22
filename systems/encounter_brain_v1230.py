# -*- coding: utf-8 -*-
"""v1.23.0: encounter-local tactics, no generated catalogs or save migration.

Never intercepts a player's damage, never overrides UOSS/authored boss scripts.
"""
import hashlib
import time

from systems.elemental_combat import mob_element_affinities_v11339, V11339_ELEMENT_ATTACKS, V11339_ELEMENT_LABELS
from systems.monster_ai import PROTECTED_FLAGS, monster_ai_eligible_v1160

_BOSS_FLAGS = ('boss', 'crypt_boss', 'mythic_crypt_boss', 'astral_boss',
               'mythic_astral_boss', 'mini_boss', 'world_boss', 'magitek_boss',
               'machine_boss', 'dungeon_boss', 'instance_boss')
_ELEMENTS = ('fire', 'ice', 'lightning', 'dark', 'poison', 'shadow', 'holy')


def boss_tactics_phase_v1230(mob, template, now=None):
    """One phase per threshold for ordinary bosses; no outgoing player damage cap."""
    if template.get('v500_ancient_profile') is not None:
        from systems.war_of_gods_bosses_v5000 import unique_phase
        return unique_phase(mob, template, now)
    if not mob or not getattr(mob, 'alive', False) or mob.hp <= 0:
        return None
    if any(template.get(flag) for flag in PROTECTED_FLAGS if flag not in ('mini_boss', 'world_boss', 'crypt_boss', 'astral_boss', 'mythic_crypt_boss', 'mythic_astral_boss')):
        return None
    if not (any(template.get(flag) for flag in _BOSS_FLAGS) or
            str(template.get('rank', '')).lower() in ('boss', 'world_boss', 'mini_boss')):
        return None
    maximum = max(1, int(getattr(mob, 'adaptive_max_hp_v11330', 0) or template.get('max_hp', 1) or 1))
    fraction = max(0, int(mob.hp)) / maximum
    custom_phases = template.get('olc_boss_phases')
    if custom_phases is not None:
        # Validated during OLC publication; legacy content never reaches here.
        target_stage = 0
        for number, rule in enumerate(custom_phases, 1):
            if fraction * 100 <= rule['hp_percent']:
                target_stage = number
    else:
        target_stage = 3 if fraction <= .25 else 2 if fraction <= .50 else 1 if fraction <= .75 else 0
    stage = max(0, int(getattr(mob, 'v1230_boss_phase', 0) or 0))
    if target_stage <= stage:
        return None
    mob.v1230_boss_phase = target_stage
    now = time.monotonic() if now is None else now
    labels = ('', 'mobilizuje się i zmienia rytm ataku',
              'przechodzi do kontrataku i wzmacnia ofensywę',
              'walczy desperacko i uderza ze zdwojoną determinacją')
    if custom_phases is not None:
        rule = custom_phases[target_stage - 1]
        mob.monster_ai_empowered_until_v1160 = now + rule['duration_seconds']
        mob.v1230_phase_attack_multiplier = rule['attack_multiplier']
        message = rule['message']
    else:
        mob.monster_ai_empowered_until_v1160 = now + (18.0 + 5.0 * target_stage)
        mob.v1230_phase_attack_multiplier = 1.12 + 0.12 * target_stage
        from systems.adventure_codex_v1270 import boss_phase_identity_v1270
        message = boss_phase_identity_v1270(template, target_stage) or labels[target_stage]
    return f"{template.get('name', 'Boss')}: FAZA {target_stage}/{len(custom_phases) if custom_phases is not None else 3} — {message}."


def tactical_element_v1230(mob, template, current_profile=None):
    """Occasional elemental technique of an ordinary physical enemy.

    Only when its authored elemental system did not already pick an ability.
    Existing gear wards, magical defence and status handling remain canonical.
    """
    if (current_profile or not mob or not getattr(mob, 'alive', False) or
            not getattr(mob, 'engaged_by', None) or
            getattr(mob, 'monster_ai_summoned_v1160', False) or
            any(template.get(flag) for flag in PROTECTED_FLAGS)):
        return current_profile
    if mob_element_affinities_v11339(template):
        return None  # Authored element choices win.
    if any(template.get(flag) for flag in PROTECTED_FLAGS):
        return None
    turn = max(0, int(getattr(mob, 'combat_turn', 0) or 0))
    # Declarative OLC v13 optional frequency; default old behaviour (4).
    interval = template.get('olc_boss_tactic_interval', 4)
    interval = interval if type(interval) is int and 2 <= interval <= 12 else 4
    from systems.live_olc4_boss_phases import eligible_boss
    if eligible_boss(template):
        from systems.live_olc21_phase_strategy import phase_setting
        interval = phase_setting(template, getattr(mob, 'v1230_boss_phase', 0),
                                 'olc_boss_phase_tactic_intervals', interval)
    if turn < interval or turn % interval:
        return None
    digest = hashlib.sha256(str(mob.template_id).encode('utf-8')).digest()
    element = _ELEMENTS[(digest[0] + turn // interval) % len(_ELEMENTS)]
    # OLC v13: deterministic selected element for *ordinary* non-scripted
    # bosses. Existing authored affinities/protected combat rules win above.
    configured_cycle = template.get('olc_boss_element_cycle')
    if any(template.get(flag) for flag in _BOSS_FLAGS):
        from systems.live_olc20_phase_tactics import boss_stage_cycle
        stage_cycle = boss_stage_cycle(template, getattr(mob, 'v1230_boss_phase', 0),
                                       'olc_boss_phase_element_cycles', _ELEMENTS)
        if stage_cycle is not None:
            configured_cycle = stage_cycle
    if (configured_cycle and any(template.get(flag) for flag in _BOSS_FLAGS) and
            isinstance(configured_cycle, (list, tuple)) and
            all(el in _ELEMENTS for el in configured_cycle)):
        element = configured_cycle[(turn // interval - 1) % len(configured_cycle)]
        configured = element
    else:
        configured = template.get('olc_boss_tactic_element')
    if configured in _ELEMENTS and any(template.get(flag) for flag in _BOSS_FLAGS):
        element = configured
    if any(template.get(flag) for flag in _BOSS_FLAGS) and not configured:
        name = str(template.get('name','')).casefold()
        if 'dragon' in name or 'smok' in name:
            element = 'fire'
        elif 'nekrom' in name or 'lich' in name:
            element = 'dark'
        elif 'burz' in name or 'grom' in name:
            element = 'lightning'
        elif 'zorz' in name or 'świat' in name:
            element = 'holy'
    spec = V11339_ELEMENT_ATTACKS[element]
    return {'element': element, 'label': V11339_ELEMENT_LABELS[element],
            'damage_multiplier': spec['damage_multiplier'],
            'text': f"Taktyczny atak {V11339_ELEMENT_LABELS[element]} — {spec['text']}",
            'spell_name': f"Atak {V11339_ELEMENT_LABELS[element]}",
            'defense_channel': 'magic'}


def ordinary_tactics_v1230(world, mob, template, now=None):
    """Combat-local decisions for ordinary mobs, including dungeon and crypt mobs.

    Bosses retain their authored encounter scripts. A support move replaces (never
    accompanies) the mob's attack; frequency depends on observed combat state.
    """
    if (not mob or not getattr(mob, 'alive', False) or not getattr(mob, 'engaged_by', None)
            or getattr(mob, 'monster_ai_summoned_v1160', False)
            or any(template.get(flag) for flag in PROTECTED_FLAGS)
            or monster_ai_eligible_v1160(mob, template)):
        return ''
    turn = max(0, int(getattr(mob, 'combat_turn', 0) or 0))
    if turn < 3:
        return ''
    now = time.monotonic() if now is None else float(now)
    if now < float(getattr(mob, 'monster_ai_next_action_v1160', 0) or 0):
        return ''
    from data.mobs import MOB_TEMPLATES
    # Room-indexed lookup: no expensive whole-world scan on each combat tick.
    allies = [candidate for candidate in world.room_mobs(mob.room_id)
              if candidate is not mob and getattr(candidate, 'alive', False)
              and candidate.engaged_by == mob.engaged_by
              and not getattr(candidate, 'monster_ai_summoned_v1160', False)]
    from systems.live_olc4_boss_phases import eligible_boss
    _olc_boss = eligible_boss(template)
    guard_threshold = (template.get('olc_boss_guard_threshold', 55) if _olc_boss else 55)
    guard_threshold = guard_threshold if type(guard_threshold) is int and 5 <= guard_threshold <= 95 else 55
    if _olc_boss:
        from systems.live_olc21_phase_strategy import phase_setting
        stage = getattr(mob, 'v1230_boss_phase', 0)
        guard_threshold = phase_setting(template, stage, 'olc_boss_phase_guard_thresholds', guard_threshold)
    injured = []
    for ally in allies:
        cap = max(1, int(getattr(ally, 'adaptive_max_hp_v11330', 0) or
                         MOB_TEMPLATES.get(ally.template_id, {}).get('max_hp', 1) or 1))
        if ally.hp * 100 <= guard_threshold * cap and now >= float(getattr(ally, 'monster_ai_guard_until_v1160', 0) or 0):
            injured.append((ally.hp / cap, ally))
    name = template.get('name', mob.template_id)
    # Wounded pack members get priority over self-buffs, but the mob cannot
    # spam a protective action or permanently avoid its regular attacks.
    from systems.live_olc4_boss_phases import eligible_boss
    _olc_boss = eligible_boss(template)
    support_interval = int(template.get('olc_boss_support_interval', 4)) if _olc_boss else 4
    support_duration = int(template.get('olc_boss_support_duration', 10)) if _olc_boss else 10
    if _olc_boss:
        support_interval = phase_setting(template, stage, 'olc_boss_phase_support_intervals', support_interval)
        support_duration = phase_setting(template, stage, 'olc_boss_phase_support_durations', support_duration)
    if injured and turn % support_interval == 0:
        # v15.20: validated OLC priority; default preserves historical AI.
        priority = template.get('olc_boss_support_priority', 'weakest') if _olc_boss else 'weakest'
        if _olc_boss:
            priority = phase_setting(template, stage, 'olc_boss_phase_support_priorities', priority)
        target = (max(injured, key=lambda pair: pair[0])[1] if priority == 'strongest'
                  else min(injured, key=lambda pair: pair[0])[1])
        target.monster_ai_guard_until_v1160 = now + support_duration
        mob.monster_ai_next_action_v1160 = now + 18.0
        return f"{name} osłania rannego sojusznika na {support_duration} sekund."
    own_cap = max(1, int(getattr(mob, 'adaptive_max_hp_v11330', 0) or template.get('max_hp', 1) or 1))
    # Hurt monsters rally earlier; healthy mobs coordinate less frequently.
    rally_hp = int(template.get('olc_boss_rally_hp_threshold', 40)) if _olc_boss else 40
    rally_hp = rally_hp if 5 <= rally_hp <= 95 else 40
    if _olc_boss:
        rally_hp = phase_setting(template, stage, 'olc_boss_phase_rally_hp_thresholds', rally_hp)
    interval = 5 if mob.hp * 100 <= rally_hp * own_cap else 7
    if _olc_boss:
        interval = int(template.get('olc_boss_rally_interval', interval))
    rally_duration = int(template.get('olc_boss_rally_duration', 12)) if _olc_boss else 12
    if _olc_boss:
        interval = phase_setting(template, stage, 'olc_boss_phase_rally_intervals', interval)
        rally_duration = phase_setting(template, stage, 'olc_boss_phase_rally_durations', rally_duration)
    if turn % interval:
        return ''
    mob.monster_ai_empowered_until_v1160 = now + rally_duration
    mob.monster_ai_next_action_v1160 = now + 18.0
    return f"{name} zmienia taktykę i przygotowuje silniejszy kontratak."


def mercenary_combo_v1230(role, all_roles, definitions):
    """Small uncapped percentage synergy; all three still take separate turns."""
    owner_type = definitions[role]['attack_type']
    other_types = {definitions[r]['attack_type'] for r in all_roles if r != role and r in definitions}
    return 1.12 if other_types and owner_type not in other_types else 1.05 if other_types else 1.0


def caravan_itinerary_v1230(now=None):
    """Stable 15-minute itineraries; no background timers or database writes."""
    from world.generation_systems import V016_TRAVELERS, v0160_traveler_room
    return [(data['name'], v0160_traveler_room(key, now)) for key, data in V016_TRAVELERS.items()]
