# -*- coding: utf-8 -*-
"""v1.80.8 — real, short-lived combat effects applied by living summons.

Status is attached to a runtime mob, never stored in the players' SQLite DB.
All owners share one status/cooldown pool on a target: a whole summon army
cannot permanently stun a boss or multiply a poison effect indefinitely.
"""
from __future__ import annotations
import random
import time

# kind: description, duration, maximum periodic pulses, proc probability
_EFFECTS = {
    'poison': ('Trucizna kobry', 12.0, 3, .32),
    'burn': ('Podpalenie', 9.0, 3, .26),
    'freeze': ('Zamrożenie', 6.0, 0, .22),
    'shock': ('Porażenie', 5.0, 0, .20),
}
# One-off control effects last only one attempted enemy action. No chaining
# from 12 elementals; both freezing and shocking share one cooldown.
_CONTROL = frozenset(('freeze', 'shock'))


def summon_effect_for_v1808(summon_type, elemental=None):
    if summon_type == 'zw_kobra':
        return 'poison'
    if not elemental:
        return ''
    return {'ogien': 'burn', 'blyskawice': 'shock',
            'lod': 'freeze', 'krysztal': 'freeze'}.get(elemental.get('element'), '')


def apply_summon_status_v1808(mob, summon_type, damage, template=None,
                              elemental=None, now=None, roll=None):
    """Attempt to apply an effect, return one concise NVDA-readable message.

    Reapplications do not refresh durations, tick power or control charges.
    This does not add a second instant hit; all ordinary damage remains intact.
    """
    effect = summon_effect_for_v1808(summon_type, elemental)
    if not effect or mob is None or not getattr(mob, 'alive', False) or int(getattr(mob, 'hp', 0)) <= 0 or int(damage) <= 0:
        return ''
    now = time.monotonic() if now is None else float(now)
    template = template or {}
    boss = bool(template.get('boss') or template.get('world_boss') or
                template.get('uoss_superboss') or template.get('v1800_chaos_boss'))
    label, duration, ticks, chance = _EFFECTS[effect]
    rank = int(elemental.get('rank', 0)) if elemental else 0
    chance = min(.45, chance + .025 * rank)
    if elemental and elemental['element'] == 'krysztal':
        chance *= .60  # crystals favor defense and freeze less often than ice
    if boss:
        chance *= .45 if effect in _CONTROL else .70
    statuses = getattr(mob, 'v1808_summon_statuses', None)
    if not isinstance(statuses, dict):
        statuses = {}
        mob.v1808_summon_statuses = statuses
    cooldowns = getattr(mob, 'v1808_summon_cooldowns', None)
    if not isinstance(cooldowns, dict):
        cooldowns = {}
        mob.v1808_summon_cooldowns = cooldowns
    for name, status in tuple(statuses.items()):
        if now >= status['until']:
            del statuses[name]
    if (effect in statuses or len(statuses) >= 2 or
            now < float(cooldowns.get(effect, 0)) or
            (effect in _CONTROL and now < float(cooldowns.get('control', 0)))):
        return ''
    roll = random.random() if roll is None else float(roll)
    if roll >= chance:
        return ''
    # DOT damage is based on this hit, rather than on the player's HP, and
    # bounded to avoid excessive damage to scale-up endgame opponents.
    max_hp = max(1, int(getattr(mob, 'adaptive_max_hp_v11330', 0) or
                        template.get('max_hp') or mob.hp))
    power = min(max(1, int(max_hp * (.004 if boss else .012))),
                max(1, int(damage * (.07 if effect == 'poison' else .05))))
    statuses[effect] = {'until': now + duration, 'next_tick': now + 3.0,
                        'ticks_left': ticks, 'power': power,
                        'skip_left': 1 if effect in _CONTROL else 0}
    cooldowns[effect] = now + duration + (16.0 if boss else 9.0)
    if effect in _CONTROL:
        cooldowns['control'] = now + (24.0 if boss else 14.0)
    if effect == 'poison':
        return f'Kobra zatruwa przeciwnika: {label}, do {ticks} impulsów.'
    if effect == 'burn':
        return f'Żywiołak Ognia podpala przeciwnika: do {ticks} impulsów.'
    if effect == 'shock':
        return 'Żywiołak Błyskawic poraża przeciwnika: może stracić jedną akcję.'
    return ('Żywiołak Kryształu skuwa przeciwnika lodem: może stracić jedną akcję.'
            if elemental and elemental['element'] == 'krysztal' else
            'Żywiołak Lodu zamraża przeciwnika: może stracić jedną akcję.')


def summon_status_enemy_turn_v1808(mob, now=None):
    """One mob action: periodic damage and at most ONE skipped action.

    Return (messages, skip_action, killed). Caller awards the kill normally.
    """
    statuses = getattr(mob, 'v1808_summon_statuses', None)
    if not isinstance(statuses, dict) or not statuses or not getattr(mob, 'alive', False):
        return (), False, False
    now = time.monotonic() if now is None else float(now)
    messages = []
    skip = False
    for kind, status in tuple(statuses.items()):
        if now >= status['until']:
            del statuses[kind]
            continue
        if kind in _CONTROL and status['skip_left']:
            status['skip_left'] = 0
            skip = True
            label = 'zamrożony' if kind == 'freeze' else 'porażony'
            messages.append(f'Przeciwnik jest {label} przez przywołanie i traci jedną akcję.')
        if kind in ('poison', 'burn') and status['ticks_left'] > 0 and now >= status['next_tick']:
            status['ticks_left'] -= 1
            status['next_tick'] = now + 3.0
            damage = min(max(0, int(mob.hp)), status['power'])
            mob.hp -= damage
            messages.append(f'{"Trucizna kobry" if kind == "poison" else "Podpalenie żywiołaka"}: {damage} obrażeń okresowych. HP przeciwnika: {max(0, mob.hp)}.')
            if mob.hp <= 0:
                return tuple(messages), True, True
    return tuple(messages), skip, False


def clear_summon_status_v1808(mob):
    mob.v1808_summon_statuses = {}
    mob.v1808_summon_cooldowns = {}
