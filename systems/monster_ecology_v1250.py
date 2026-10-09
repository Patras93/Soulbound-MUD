# -*- coding: utf-8 -*-
"""Soulbound 1.25: species tactics and adaptive enemy skill cadence.

Pure encounter-local decisions, never override authored boss scripts and never
modify player outgoing damage. Finite reaction cadence protects low-level solos.
"""
import time
from systems.monster_ai import PROTECTED_FLAGS

PACK = ('wilk', 'wolf', 'szakal', 'hiena', 'hound', 'ogar')
DRAGON = ('smok', 'dragon', 'wyvern', 'drake')
UNDEAD = ('szkielet', 'skeleton', 'zombie', 'upior', 'widmo', 'ghoul', 'undead', 'trup', 'licz')
CASTER = ('mag', 'mage', 'czarod', 'sorcer', 'kaplan', 'priest', 'shaman', 'szaman')

def species_v1250(template):
    identity = (str(template.get('name', '')) + ' ' + str(template.get('creature_type', ''))).casefold()
    if any(w in identity for w in DRAGON): return 'dragon'
    if any(w in identity for w in PACK): return 'pack'
    if any(w in identity for w in UNDEAD): return 'undead'
    if template.get('damage_type') == 'magic' or any(w in identity for w in CASTER): return 'caster'
    return 'tactician'

def ecology_turn_v1250(world, mob, template, now=None):
    """One finite special instead of a normal action; returns brief Polish message."""
    if (not mob or not getattr(mob, 'alive', False) or not getattr(mob, 'engaged_by', None)
        or getattr(mob, 'monster_ai_summoned_v1160', False)
        or any(template.get(f) for f in PROTECTED_FLAGS)
        or template.get('boss') or template.get('mini_boss') or template.get('world_boss')):
        return ''
    turn = max(0, int(getattr(mob, 'combat_turn', 0) or 0))
    if turn < 4 or turn % 4: return ''
    now = time.monotonic() if now is None else float(now)
    if now < float(getattr(mob, 'v1250_ecology_next', 0) or 0): return ''
    kind = species_v1250(template)
    name = str(template.get('name') or mob.template_id)
    allies = [a for a in world.mobs.values() if a is not mob and getattr(a, 'alive', False)
              and a.room_id == mob.room_id and a.engaged_by == mob.engaged_by]
    if kind == 'pack':
        if not any(species_v1250(world.mob_templates_for_ai_v1160(a)) == 'pack' for a in allies):
            return ''  # A lone wolf is not a pack.
        mob.monster_ai_empowered_until_v1160 = now + 12
        mob.v1230_phase_attack_multiplier = 1.22
        text = f'{name} koordynuje natarcie stada i przygotowuje mocniejszy atak.'
    elif kind == 'undead':
        if getattr(mob, 'v1250_recovered', False): return ''
        maximum = max(1, int(getattr(mob, 'adaptive_max_hp_v11330', 0) or template.get('max_hp', 1)))
        if mob.hp * 100 >= maximum * 55: return ''
        gain = min(maximum - mob.hp, max(1, (maximum * 14) // 100))
        if gain <= 0: return ''
        mob.hp += gain
        mob.v1250_recovered = True
        text = f'{name} próbuje odrodzić się z popiołów: odzyskuje {gain} HP (raz na walkę).'
    elif kind == 'caster':
        target = min((a for a in [mob] + allies if a.hp > 0), key=lambda a: a.hp / max(1, int(getattr(a, 'adaptive_max_hp_v11330', 0) or world.mob_templates_for_ai_v1160(a).get('max_hp', 1))), default=None)
        if not target: return ''
        maxhp = max(1, int(getattr(target, 'adaptive_max_hp_v11330', 0) or world.mob_templates_for_ai_v1160(target).get('max_hp', 1)))
        if target.hp * 100 >= maxhp * 65: return ''
        gain = min(maxhp - target.hp, max(1, (maxhp * 12) // 100))
        target.hp += gain
        text = f'{name} leczy rannego sojusznika: +{gain} HP.'
    elif kind == 'dragon':
        mob.monster_ai_empowered_until_v1160 = now + 12
        mob.v1230_phase_attack_multiplier = 1.25
        text = f'{name} gromadzi żywiołową energię przed kolejnym atakiem.'
    else:
        if not allies: return ''
        mob.monster_ai_guard_until_v1160 = now + 8
        text = f'{name} zmienia taktykę i osłania się przed ciosem.'
    mob.v1250_ecology_next = now + 20
    return text


def adaptive_skills_v1250(mob, template, owner_power, base_damage):
    """Small adaptive cadence bonus; no one-shot escalation for beginners."""
    if any(template.get(f) for f in PROTECTED_FLAGS) or template.get('training_dummy'):
        return 1.0
    ratio = max(1.0, float(owner_power or 0) / max(1.0, float(base_damage or 1)))
    # At high power monsters grow tougher and diversify attacks, without a low-level spike.
    from math import log2
    attack = 1.0 + min(.36, .035 * max(0.0, log2(ratio)))
    turn = max(0, int(getattr(mob, 'combat_turn', 0) or 0))
    if turn >= 5 and turn % 5 == 0:
        attack *= 1.10  # Faster combination every fifth turn, not extra AoE hits.
    from systems.team_learning_v1260 import enemy_team_pressure_v1260
    return attack * enemy_team_pressure_v1260(mob, template)


def adaptive_defense_v1250(mob, template, now=None):
    """Temporary guard scales with encounter threat, with long cooldown."""
    if (not mob or not mob.alive or any(template.get(f) for f in PROTECTED_FLAGS)
        or template.get('training_dummy')): return ''
    turn = max(0, int(getattr(mob, 'combat_turn', 0) or 0))
    power = float(getattr(mob, 'adaptive_party_dps_v11330', 0) or 0)
    base = max(1., float(template.get('damage', 1) or 1))
    if turn < 7 or turn % 7 or power < base * 50: return ''
    now = time.monotonic() if now is None else float(now)
    if now < float(getattr(mob, 'monster_ai_guard_until_v1160', 0) or 0): return ''
    mob.monster_ai_guard_until_v1160 = now + 5
    return f"{template.get('name', mob.template_id)} przyjmuje obronną postawę na 5 sekund."


def adaptive_cadence_v1250(mobs, templates, normal_interval):
    """Faster enemy responses only when the party hugely outscales the baseline."""
    baseline = max(.45, float(normal_interval or 1.0))
    for mob in mobs:
        template = templates.get(getattr(mob, 'template_id', ''), {})
        if any(template.get(f) for f in PROTECTED_FLAGS): continue
        power = float(getattr(mob, 'adaptive_party_dps_v11330', 0) or 0)
        base = max(1., float(template.get('damage', 1) or 1))
        if power > 100 * base:
            return max(.45, baseline * .86)
    return baseline
