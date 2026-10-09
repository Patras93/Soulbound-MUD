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
    if not mob or not getattr(mob, 'alive', False) or mob.hp <= 0:
        return None
    if any(template.get(flag) for flag in PROTECTED_FLAGS if flag not in ('mini_boss', 'world_boss', 'crypt_boss', 'astral_boss', 'mythic_crypt_boss', 'mythic_astral_boss')):
        return None
    if not (any(template.get(flag) for flag in _BOSS_FLAGS) or
            str(template.get('rank', '')).lower() in ('boss', 'world_boss', 'mini_boss')):
        return None
    maximum = max(1, int(getattr(mob, 'adaptive_max_hp_v11330', 0) or template.get('max_hp', 1) or 1))
    fraction = max(0, int(mob.hp)) / maximum
    target_stage = 3 if fraction <= .25 else 2 if fraction <= .50 else 1 if fraction <= .75 else 0
    stage = max(0, int(getattr(mob, 'v1230_boss_phase', 0) or 0))
    if target_stage <= stage:
        return None
    mob.v1230_boss_phase = target_stage
    now = time.monotonic() if now is None else now
    mob.monster_ai_empowered_until_v1160 = now + (18.0 + 5.0 * target_stage)
    mob.v1230_phase_attack_multiplier = 1.12 + 0.12 * target_stage
    labels = ('', 'mobilizuje się i zmienia rytm ataku',
              'przechodzi do kontrataku i wzmacnia ofensywę',
              'walczy desperacko i uderza ze zdwojoną determinacją')
    from systems.adventure_codex_v1270 import boss_phase_identity_v1270
    unique = boss_phase_identity_v1270(template, target_stage)
    return f"{template.get('name', 'Boss')}: FAZA {target_stage}/3 — {unique or labels[target_stage]}."


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
    if turn < 4 or turn % 4:
        return None
    digest = hashlib.sha256(str(mob.template_id).encode('utf-8')).digest()
    element = _ELEMENTS[(digest[0] + turn // 4) % len(_ELEMENTS)]
    if any(template.get(flag) for flag in _BOSS_FLAGS):
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
    """Every sixth melee action: defend a wounded ally or rally the pack.

    Keeps the original specialist-Monster-AI eligibility and audits intact.
    Returns a message only when the action REPLACES the basic mob attack.
    """
    turn = max(0, int(getattr(mob, 'combat_turn', 0) or 0))
    if (not mob or not getattr(mob, 'alive', False) or not getattr(mob, 'engaged_by', None)
            or getattr(mob, 'monster_ai_summoned_v1160', False)
            or any(template.get(flag) for flag in PROTECTED_FLAGS)
            or monster_ai_eligible_v1160(mob, template)
            or turn < 6 or turn % 6):
        return ''
    now = time.monotonic() if now is None else float(now)
    if now < float(getattr(mob, 'monster_ai_next_action_v1160', 0) or 0):
        return ''
    from data.mobs import MOB_TEMPLATES
    allies = [candidate for candidate in world.mobs.values()
              if candidate is not mob and getattr(candidate, 'alive', False)
              and candidate.room_id == mob.room_id and candidate.engaged_by == mob.engaged_by
              and not getattr(candidate, 'monster_ai_summoned_v1160', False)]
    injured = [ally for ally in allies if ally.hp * 100 < 65 * max(1, int(
               getattr(ally, 'adaptive_max_hp_v11330', 0) or
               MOB_TEMPLATES.get(ally.template_id, {}).get('max_hp', 1) or 1))]
    name = template.get('name', mob.template_id)
    if injured:
        target = min(injured, key=lambda ally: ally.hp)
        target.monster_ai_guard_until_v1160 = now + 10.0
        mob.monster_ai_next_action_v1160 = now + 18.0
        return f"{name} osłania rannego sojusznika na 10 sekund."
    mob.monster_ai_empowered_until_v1160 = now + 12.0
    mob.monster_ai_next_action_v1160 = now + 18.0
    return f"{name} mobilizuje się do silniejszego kontrataku."


def mercenary_combo_v1230(role, all_roles, definitions):
    """Small uncapped percentage synergy; all three still take separate turns."""
    owner_type = definitions[role]['attack_type']
    other_types = {definitions[r]['attack_type'] for r in all_roles if r != role and r in definitions}
    return 1.12 if other_types and owner_type not in other_types else 1.05 if other_types else 1.0


def caravan_itinerary_v1230(now=None):
    """Stable 15-minute itineraries; no background timers or database writes."""
    from world.generation_systems import V016_TRAVELERS, v0160_traveler_room
    return [(data['name'], v0160_traveler_room(key, now)) for key, data in V016_TRAVELERS.items()]
